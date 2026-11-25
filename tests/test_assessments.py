import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
import psycopg

from services.api.main import app
from services.db.migrate import migrate


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "requires a disposable PostgreSQL database")
class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ["TEST_DATABASE_URL"]
        self.enterContext(patch.dict(os.environ, DATABASE_URL=self.dsn, ENABLE_ASSESSMENT_INTAKE="1"))
        migrate(self.dsn)
        self.client = self.enterContext(TestClient(app, base_url="https://testserver"))
        self.client.post("/v1/session").raise_for_status()
        self.body = {"kind": "url", "url": "https://example.invalid/private", "processing_consent": True}

    def submit(self, key, **changes):
        return self.client.post("/v1/assessments", headers={"Idempotency-Key": key}, json=self.body | changes)

    def test_concurrent_replays_scope_and_outbox(self):
        with ThreadPoolExecutor(4) as pool:
            responses = list(pool.map(self.submit, ["same"] * 4))
        self.assertEqual({r.status_code for r in responses}, {202})
        receipt = responses[0].json()
        self.assertTrue(all(r.json() == receipt for r in responses))
        target = "/v1/assessments/" + receipt["assessment_id"]
        self.assertEqual(self.client.get(target).json(), receipt)
        self.assertEqual(self.submit("same", locale="ur").status_code, 409)
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute("SELECT state, published_at FROM jobs JOIN job_outbox ON jobs.id=job_id "
                                "WHERE assessment_id=%s", (receipt["assessment_id"],)).fetchall()
        self.assertEqual(rows, [("queued", None)])
        self.client.cookies.clear()
        self.assertEqual(self.submit("same").status_code, 401)
        self.client.post("/v1/session").raise_for_status()
        self.assertNotEqual(self.submit("same").json()["assessment_id"], receipt["assessment_id"])
        hidden = self.client.get(target)
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(hidden.json(), self.client.get("/v1/assessments/" + str(uuid4())).json())

    def test_concurrent_quota_and_replay(self):
        for i in range(9):
            self.assertEqual(self.submit(str(i)).status_code, 202)
        with ThreadPoolExecutor(4) as pool:
            codes = [r.status_code for r in pool.map(self.submit, ["a", "b", "c", "d"])]
        self.assertCountEqual(codes, [202, 429, 429, 429])
        self.assertEqual(self.submit("0").status_code, 202)

    def test_rejected_requests(self):
        path = "/v1/assessments"
        self.assertEqual(self.client.post(path, content="abc").status_code, 415)
        self.assertEqual(self.client.post(path, json=self.body, headers={"Origin": "https://other.invalid"}).status_code, 403)
        self.assertEqual(self.submit("key", url="a" * 270000).status_code, 413)
        invalid = self.submit("key", owner="private-marker")
        self.assertEqual(invalid.status_code, 422)
        self.assertNotIn("private-marker", invalid.text)
        self.assertEqual(self.client.post(path, json=self.body).status_code, 422)
        with patch.dict(os.environ, ENABLE_ASSESSMENT_INTAKE="0"):
            self.assertEqual(self.submit("key").status_code, 503)

    def test_failed_job_insert_rolls_back_assessment_and_key(self):
        self.submit("existing").raise_for_status()
        with psycopg.connect(self.dsn) as conn:
            job_id, = conn.execute("SELECT id FROM jobs LIMIT 1").fetchone()
        candidate = uuid4()
        with patch("services.api.assessments.uuid4", side_effect=[candidate, job_id]):
            with self.assertRaises(psycopg.errors.UniqueViolation):
                self.submit("retry")
        with psycopg.connect(self.dsn) as conn:
            self.assertIsNone(conn.execute("SELECT id FROM assessments WHERE id=%s", (candidate,)).fetchone())
        self.assertEqual(self.submit("retry").status_code, 202)

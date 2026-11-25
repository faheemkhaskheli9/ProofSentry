import hashlib
import os
import unittest
from unittest.mock import patch


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "requires a disposable PostgreSQL database")
class GuestIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from fastapi.testclient import TestClient
        from services.api.main import app
        from services.api.sessions import COOKIE
        from services.db.migrate import migrate

        cls.dsn = os.environ["TEST_DATABASE_URL"]
        cls.cookie = COOKIE
        cls.connect = staticmethod(psycopg.connect)
        cls.client = TestClient(app, base_url="https://testserver")
        cls.addClassCleanup(cls.client.close)
        settings = patch.dict(os.environ, DATABASE_URL=cls.dsn, PUBLIC_ORIGIN="https://testserver")
        settings.start()
        cls.addClassCleanup(settings.stop)
        migrate(cls.dsn)
        migrate(cls.dsn)

    def setUp(self):
        self.client.cookies.clear()

    def test_session_lifecycle(self):
        self.assertEqual(self.client.get("/v1/session").status_code, 401)
        first = self.client.post("/v1/session", headers={"Origin": "https://testserver"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers["cache-control"], "no-store")
        for attribute in ("secure", "httponly", "samesite=strict", "path=/"):
            self.assertIn(attribute, first.headers["set-cookie"].lower())
        key = hashlib.sha256(first.cookies[self.cookie].encode()).digest()
        self.assertEqual(self.client.get("/v1/session").json(), first.json())
        repeated = self.client.post("/v1/session")
        self.assertEqual(repeated.json(), first.json())
        self.assertNotIn("set-cookie", repeated.headers)
        with self.connect(self.dsn) as conn:
            owner, = conn.execute("SELECT id FROM guest_principals WHERE token_digest=%s", (key,)).fetchone()
            conn.execute("UPDATE guest_principals SET expires_at=now() WHERE id=%s", (owner,))
        self.assertEqual(self.client.get("/v1/session").status_code, 401)
        replacement = self.client.post("/v1/session")
        new_key = hashlib.sha256(replacement.cookies[self.cookie].encode()).digest()
        with self.connect(self.dsn) as conn:
            new_owner, = conn.execute("SELECT id FROM guest_principals WHERE token_digest=%s", (new_key,)).fetchone()
        self.assertNotEqual(new_owner, owner)

    def test_rejected_origin_and_unknown_credentials(self):
        for headers in ({"Origin": "https://other.invalid"}, {"Sec-Fetch-Site": "cross-site"}):
            response = self.client.post("/v1/session", headers=headers)
            self.assertEqual(response.status_code, 403)
            self.assertNotIn("set-cookie", response.headers)
        for token in ("malformed", "x" * 43):
            self.client.cookies.set(self.cookie, token)
            self.assertEqual(self.client.get("/v1/session").status_code, 401)

"""Persist guest intake and its dispatch reference in the same transaction."""

import hmac
import os
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

import psycopg
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel

from packages.contracts.intake import Intake
from services.api.sessions import COOKIE, digest, require_guest, require_trusted_origin

NO_STORE = {"Cache-Control": "no-store"}
GUEST_QUOTA = 10


class IntakeRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def bounded_intake(request: Request):
            if request.method != "POST":
                return await handler(request)
            if os.environ.get("ENABLE_ASSESSMENT_INTAKE") != "1":
                raise HTTPException(503, "Assessment intake disabled", headers=NO_STORE)
            require_trusted_origin(request)
            if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
                raise HTTPException(415, "Expected JSON", headers=NO_STORE)
            size = 0

            async def receive():
                nonlocal size
                message = await request.receive()
                size += len(message.get("body", b""))
                if size > 256 * 1024:
                    raise HTTPException(413, "Submission too large", headers=NO_STORE)
                return message

            try:
                return await handler(Request(request.scope, receive))
            except RequestValidationError as exc:
                status = 400 if any(e["type"] == "json_invalid" for e in exc.errors()) else 422
                raise HTTPException(status, "Invalid submission or idempotency key", headers=NO_STORE) from None

        return bounded_intake


router = APIRouter(prefix="/v1/assessments", route_class=IntakeRoute)


class Receipt(BaseModel):
    assessment_id: UUID
    status: str
    poll_after_seconds: int = 5


@router.post("", status_code=202)
def create_assessment(
    request: Request, response: Response, submission: Intake,
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")],
) -> Receipt:
    credential = digest(request)
    if credential is None:
        raise HTTPException(401, "Guest session required", headers=NO_STORE)
    content = submission.model_dump_json().encode()
    fingerprint = hmac.digest(request.cookies[COOKIE].encode("ascii"), content, "sha256")
    response.headers.update(NO_STORE)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        # Serialize quota and replay decisions for this guest, including concurrent retries.
        owner = conn.execute(
            "SELECT id FROM guest_principals WHERE token_digest=%s AND expires_at > clock_timestamp() FOR UPDATE",
            (credential,),
        ).fetchone()
        if owner is None:
            raise HTTPException(401, "Guest session required", headers=NO_STORE)
        owner_id, = owner
        prior = conn.execute(
            "SELECT id, status, request_digest FROM assessments WHERE owner_id=%s AND idempotency_key=%s",
            (owner_id, idempotency_key),
        ).fetchone()
        if prior:
            if prior[2] != fingerprint:
                raise HTTPException(409, "Key already used for a different submission", headers=NO_STORE)
            return Receipt(assessment_id=prior[0], status=prior[1])
        count, = conn.execute("SELECT count(*) FROM assessments WHERE owner_id=%s", (owner_id,)).fetchone()
        if count >= GUEST_QUOTA:
            raise HTTPException(429, "Guest session quota reached", headers=NO_STORE)
        assessment_id, job_id = uuid4(), uuid4()
        conn.execute(
            "INSERT INTO assessments (id, owner_id, idempotency_key, request_digest) VALUES (%s,%s,%s,%s)",
            (assessment_id, owner_id, idempotency_key, fingerprint),
        )
        conn.execute("INSERT INTO assessment_inputs VALUES (%s,%s)", (assessment_id, content))
        conn.execute("INSERT INTO jobs (id, assessment_id, detector_key) VALUES (%s,%s,%s)",
                     (job_id, assessment_id, submission.kind))
        conn.execute("INSERT INTO job_outbox (job_id) VALUES (%s)", (job_id,))
    return Receipt(assessment_id=assessment_id, status="queued")


@router.get("/{assessment_id}")
def assessment_status(
    assessment_id: UUID, response: Response, principal: tuple[UUID, datetime] = Depends(require_guest),
) -> Receipt:
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        row = conn.execute("SELECT status FROM assessments WHERE owner_id=%s AND id=%s",
                           (principal[0], assessment_id)).fetchone()
    if row is None:
        raise HTTPException(404, "Assessment not found", headers=NO_STORE)
    response.headers.update(NO_STORE)
    return Receipt(assessment_id=assessment_id, status=row[0])

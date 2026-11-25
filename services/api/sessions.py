"""Guest credentials are random bearer secrets. PostgreSQL stores only their digests."""

import hashlib
import os
import re
import secrets
from datetime import UTC, datetime
from uuid import UUID, uuid4

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

router = APIRouter(prefix="/v1")
COOKIE = "__Host-proofsentry_guest"


class Guest(BaseModel):
    expires_at: datetime


def digest(request: Request) -> bytes | None:
    token = request.cookies.get(COOKIE, "")
    if re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        return hashlib.sha256(token.encode("ascii")).digest()
    return None


def lookup(conn: psycopg.Connection, key: bytes | None) -> tuple[UUID, datetime] | None:
    return conn.execute(
        "SELECT id, expires_at FROM guest_principals WHERE token_digest = %s AND expires_at > now()",
        (key,),
    ).fetchone()


def require_guest(request: Request) -> tuple[UUID, datetime]:
    key = digest(request)
    if key is not None:
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            principal = lookup(conn, key)
            if principal:
                return principal
    raise HTTPException(401, "Guest session required", headers={"Cache-Control": "no-store"})


@router.post("/session", response_model=Guest)
def start_guest(request: Request, response: Response) -> Guest:
    origin = request.headers.get("origin")
    if ((origin is not None and origin != os.environ.get("PUBLIC_ORIGIN"))
            or request.headers.get("sec-fetch-site") == "cross-site"):
        raise HTTPException(403, "Untrusted origin")
    response.headers["Cache-Control"] = "no-store"
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        principal = lookup(conn, digest(request))
        if principal:
            return Guest(expires_at=principal[1])
        conn.execute(
            "DELETE FROM guest_principals WHERE id IN (SELECT id FROM guest_principals "
            "WHERE expires_at <= now() ORDER BY expires_at LIMIT 100 FOR UPDATE SKIP LOCKED)"
        )
        token = secrets.token_urlsafe(32)
        expiry, = conn.execute(
            "INSERT INTO guest_principals (id, token_digest) VALUES (%s, %s) RETURNING expires_at",
            (uuid4(), hashlib.sha256(token.encode("ascii")).digest()),
        ).fetchone()
        response.set_cookie(COOKIE, token, expires=expiry.astimezone(UTC), secure=True, httponly=True, samesite="strict")
        return Guest(expires_at=expiry)


@router.get("/session", response_model=Guest)
def current_guest(response: Response, principal: tuple[UUID, datetime] = Depends(require_guest)) -> Guest:
    response.headers["Cache-Control"] = "no-store"
    return Guest(expires_at=principal[1])

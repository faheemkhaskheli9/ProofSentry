"""Apply ordered PostgreSQL migrations in one serialized transaction."""

import os
from hashlib import sha256
from pathlib import Path

import psycopg


def migrate(dsn: str) -> None:
    with psycopg.connect(dsn) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(718452630)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name text PRIMARY KEY, checksum text NOT NULL
            )
        """)
        applied = dict(conn.execute("SELECT name, checksum FROM schema_migrations"))
        files = sorted(Path(__file__).with_name("migrations").glob("*.sql"))
        if sorted(applied) != [path.name for path in files[:len(applied)]]:
            raise RuntimeError("Unexpected migration history")
        for path in files:
            source = path.read_bytes()
            checksum = sha256(source).hexdigest()
            if path.name in applied:
                if applied[path.name] != checksum:
                    raise RuntimeError(f"Changed migration: {path.name}")
                continue
            conn.execute(source.decode("utf-8"))
            conn.execute("INSERT INTO schema_migrations VALUES (%s, %s)", (path.name, checksum))


if __name__ == "__main__":
    migrate(os.environ["DATABASE_URL"])

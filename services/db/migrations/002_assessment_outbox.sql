CREATE TABLE assessments (
    id uuid PRIMARY KEY,
    owner_id uuid NOT NULL REFERENCES guest_principals ON DELETE CASCADE,
    idempotency_key text NOT NULL,
    request_digest bytea NOT NULL,
    status text NOT NULL DEFAULT 'queued',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (owner_id, idempotency_key)
);

-- Keep the transient JSON input independently purgeable after processing.
CREATE TABLE assessment_inputs (
    assessment_id uuid PRIMARY KEY REFERENCES assessments ON DELETE CASCADE,
    content bytea NOT NULL
);

CREATE TABLE jobs (
    id uuid PRIMARY KEY,
    assessment_id uuid NOT NULL REFERENCES assessments ON DELETE CASCADE,
    generation integer NOT NULL DEFAULT 1,
    detector_key text NOT NULL,
    state text NOT NULL DEFAULT 'queued',
    UNIQUE (assessment_id, generation, detector_key)
);

CREATE TABLE job_outbox (
    job_id uuid PRIMARY KEY REFERENCES jobs ON DELETE CASCADE,
    available_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz
);
CREATE INDEX job_outbox_pending ON job_outbox (available_at) WHERE published_at IS NULL;

CREATE TABLE guest_principals (
    id uuid PRIMARY KEY,
    token_digest bytea NOT NULL UNIQUE CHECK (octet_length(token_digest) = 32),
    expires_at timestamptz NOT NULL DEFAULT (CURRENT_TIMESTAMP + interval '24 hours')
);
CREATE INDEX guest_principals_expiry ON guest_principals (expires_at);

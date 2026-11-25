"""Draft v1 JSON intake. Multipart media gets its own contract at quarantine rollout."""

from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    locale: str = Field(default="en", pattern=r"^[a-zA-Z]{2,8}(-[a-zA-Z0-9]{1,8})*$", max_length=63)
    country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    # Processing consent never grants permission to reuse evidence.
    processing_consent: Literal[True]

    @field_validator("processing_consent", mode="before")
    @classmethod
    def explicit_consent(cls, value: object) -> object:
        if value is not True:
            raise ValueError("Explicit processing consent required")
        return value


class TextSubmission(Submission):
    kind: Literal["text"]
    text: str = Field(min_length=1, max_length=20_000)

    @field_validator("text")
    @classmethod
    def require_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Empty text")
        return value


class URLSubmission(Submission):
    kind: Literal["url"]
    url: str = Field(min_length=1, max_length=4096)

    @field_validator("url")
    @classmethod
    def require_http_url(cls, value: str) -> str:
        if "\\" in value or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("Ambiguous URL")
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("HTTP(S) URL with a host required")
        # Accessing port also checks its syntax and range.
        _ = parts.port
        return value


Intake = Annotated[TextSubmission | URLSubmission, Field(discriminator="kind")]
intake_adapter = TypeAdapter(Intake)

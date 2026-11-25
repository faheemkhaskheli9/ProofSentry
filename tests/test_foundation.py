import json
from pathlib import Path
import unittest

from pydantic import ValidationError

from packages.contracts.intake import intake_adapter
from packages.contracts.schema import render

ROOT = Path(__file__).resolve().parents[1]


class IntakeTests(unittest.TestCase):
    def test_published_schema(self):
        self.assertEqual((ROOT / "packages/contracts/intake-v1.schema.json").read_text(), render())

    def test_synthetic_corpus(self):
        cases = json.loads((ROOT / "evaluation/intake-v1.json").read_text())
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        for case in cases:
            with self.subTest(case=case["id"]):
                if case["valid"]:
                    submission = intake_adapter.validate_python(case["input"])
                    self.assertEqual(submission.kind, case["input"]["kind"])
                else:
                    with self.assertRaises(ValidationError):
                        intake_adapter.validate_python(case["input"])

    def test_boundaries_and_original_text(self):
        for kind, prefix, limit in [("text", "  کتاب", 20000), ("url", "https://example.invalid/", 4096)]:
            value = prefix + "a" * (limit - len(prefix))
            data = {"kind": kind, kind: value, "processing_consent": True}
            self.assertEqual(getattr(intake_adapter.validate_python(data), kind), value)
            with self.assertRaises(ValidationError):
                intake_adapter.validate_python({**data, kind: value + "a"})

    def test_rejected_inputs(self):
        text = {"kind": "text", "text": "Hello", "processing_consent": True}
        for changes in ({"owner": "other"}, {"text": "  "}, {"processing_consent": 1}, {"kind": "image"}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                intake_adapter.validate_python({**text, **changes})
        for url in ("https:///path", "http://example.invalid:99999", " https://example.invalid"):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                intake_adapter.validate_python({"kind": "url", "url": url, "processing_consent": True})

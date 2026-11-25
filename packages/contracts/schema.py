"""Export the machine-readable contract with python -m packages.contracts.schema."""

import json

from .intake import intake_adapter


def render() -> str:
    return json.dumps(intake_adapter.json_schema(), ensure_ascii=False, indent=2) + "\n"


if __name__ == "__main__":
    print(render(), end="")

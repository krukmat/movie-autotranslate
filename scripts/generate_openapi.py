#!/usr/bin/env python3
"""Generate OpenAPI schemas (JSON + YAML) from the FastAPI app."""

import json
from pathlib import Path

import yaml

import sys
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))
sys.path.append(str(root / "backend"))

from fastapi.openapi.utils import get_openapi  # noqa: E402
from app.main import app  # noqa: E402

schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
json_path = root / "docs" / "openapi.json"
yaml_path = root / "docs" / "openapi.yaml"
json_path.write_text(json.dumps(schema, indent=2))
yaml_path.write_text(yaml.safe_dump(schema, sort_keys=False))
print(f"Wrote {json_path} and {yaml_path}")

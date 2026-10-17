"""Write the FastAPI OpenAPI schema to a file without starting the server.

Usage: uv run python scripts/export_openapi.py <output.json>
"""

import json
import sys
from pathlib import Path

from hookd_api.main import app

Path(sys.argv[1]).write_text(json.dumps(app.openapi(), indent=2))

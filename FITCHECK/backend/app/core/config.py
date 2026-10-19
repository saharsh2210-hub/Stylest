import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = Path(os.getenv("FITCHECK_UPLOAD_DIR") or BACKEND_ROOT / "uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIST = Path(
    os.getenv("FITCHECK_FRONTEND_DIST")
    or BACKEND_ROOT.parent / "frontend" / "dist"
)

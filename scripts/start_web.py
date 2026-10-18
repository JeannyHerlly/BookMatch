import os
from pathlib import Path

from ensure_dataset import ensure_dataset


DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(DATA_DIR / "huggingface"))

try:
    ensure_dataset()
except RuntimeError as error:
    raise SystemExit(str(error)) from None

from waitress import serve

from app import app


try:
    port = int(os.environ.get("PORT", "10000"))
except ValueError:
    raise SystemExit("PORT must be a valid integer.") from None

serve(app, host="0.0.0.0", port=port)

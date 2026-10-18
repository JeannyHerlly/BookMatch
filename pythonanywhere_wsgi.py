import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = Path.home() / ".local" / "share" / "bookmatch"
SECRETS_FILE = Path.home() / ".bookmatch-secrets"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

os.environ.setdefault("DATA_DIR", str(DATA_DIR))
os.environ.setdefault("HF_HOME", str(DATA_DIR / "huggingface"))
os.environ.setdefault(
    "BOOK_DATA_URL",
    "https://huggingface.co/datasets/"
    "Jeanny26/processed_books_with_bestsellers.csv/resolve/main/"
    "processed_books_with_bestseller_award.csv?download=true",
)

if SECRETS_FILE.exists():
    for line in SECRETS_FILE.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == "BOOK_DATA_TOKEN":
            os.environ.setdefault(name.strip(), value.strip())

from ensure_dataset import ensure_dataset

ensure_dataset()

from app import app as application

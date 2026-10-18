import csv
import hashlib
import os
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


REQUIRED_COLUMNS = {
    "google_id",
    "title",
    "authors",
    "categories",
    "description",
    "thumbnail",
    "published_date",
    "title_clean",
    "author_clean",
    "category_clean",
    "author_set",
    "is_award_winner",
    "award_names",
    "is_bestseller",
}


def validate_dataset(path: Path) -> None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as dataset_file:
            reader = csv.reader(dataset_file)
            columns = next(reader, None)
    except (OSError, UnicodeError, csv.Error) as error:
        raise RuntimeError(
            f"Cannot read the book dataset at {path}."
        ) from error

    if not columns:
        raise RuntimeError(f"The book dataset at {path} is empty.")

    missing = sorted(REQUIRED_COLUMNS.difference(columns))
    if missing:
        raise RuntimeError(
            "The processed book dataset is missing required columns: "
            + ", ".join(missing)
        )


def download_dataset(destination: Path, url: str, token: str) -> None:
    parsed_url = urlparse(url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise RuntimeError("BOOK_DATA_URL must be a valid HTTPS download URL.")

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    expected_sha256 = os.environ.get("BOOK_DATA_SHA256", "").strip().lower()
    digest = hashlib.sha256()

    temporary_path = None
    try:
        with urlopen(request, timeout=120) as response:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                while chunk := response.read(1024 * 1024):
                    temporary_file.write(chunk)
                    digest.update(chunk)

        if temporary_path.stat().st_size == 0:
            raise RuntimeError("The downloaded book dataset is empty.")

        if expected_sha256 and digest.hexdigest() != expected_sha256:
            raise RuntimeError(
                "The downloaded book dataset does not match BOOK_DATA_SHA256."
            )

        validate_dataset(temporary_path)
        temporary_path.replace(destination)
    except (HTTPError, URLError, TimeoutError, OSError, csv.Error) as error:
        raise RuntimeError(
            "Could not download the processed book dataset. Check "
            "BOOK_DATA_URL and BOOK_DATA_TOKEN."
        ) from None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def ensure_dataset() -> Path:
    data_dir = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
    destination = data_dir / "processed_books_with_bestsellers.csv"

    if destination.exists():
        validate_dataset(destination)
        return destination

    url = os.environ.get("BOOK_DATA_URL", "").strip()
    if not url:
        raise RuntimeError(
            f"Required processed dataset not found at {destination}. "
            "Provide it there or set BOOK_DATA_URL to an HTTPS download URL."
        )

    data_dir.mkdir(parents=True, exist_ok=True)
    download_dataset(
        destination,
        url,
        os.environ.get("BOOK_DATA_TOKEN", "").strip(),
    )
    return destination

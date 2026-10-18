"""Fetch book metadata from the Google Books volumes API into a CSV."""

import argparse
import csv
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://www.googleapis.com/books/v1/volumes"
USER_AGENT = "BookMatchResearch/1.0 (Google Books metadata collection)"
PAGE_SIZE = 40
TIMEOUT_SECONDS = 30
FIELDS = (
    "google_id",
    "title",
    "subtitle",
    "authors",
    "publisher",
    "published_date",
    "description",
    "categories",
    "page_count",
    "language",
    "isbn_10",
    "isbn_13",
    "thumbnail",
)


def get_page(query: str, start_index: int, api_key: str) -> dict:
    params = {
        "q": query,
        "startIndex": start_index,
        "maxResults": PAGE_SIZE,
        "printType": "books",
    }
    if api_key:
        params["key"] = api_key
    request = Request(
        f"{API_URL}?{urlencode(params)}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"Google Books API returned HTTP {error.code} for query "
            f"{query!r}; check the query, API quota, and API key."
        ) from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Could not retrieve Google Books results for query {query!r}."
        ) from error


def volume_to_row(volume: dict) -> dict:
    info = volume.get("volumeInfo") or {}
    identifiers = {
        identifier.get("type"): identifier.get("identifier", "")
        for identifier in info.get("industryIdentifiers", [])
    }
    return {
        "google_id": volume.get("id", ""),
        "title": info.get("title", ""),
        "subtitle": info.get("subtitle", ""),
        "authors": ", ".join(info.get("authors") or []),
        "publisher": info.get("publisher", ""),
        "published_date": info.get("publishedDate", ""),
        "description": info.get("description", ""),
        "categories": ", ".join(info.get("categories") or []),
        "page_count": info.get("pageCount", ""),
        "language": info.get("language", ""),
        "isbn_10": identifiers.get("ISBN_10", ""),
        "isbn_13": identifiers.get("ISBN_13", ""),
        "thumbnail": (info.get("imageLinks") or {}).get("thumbnail", ""),
    }


def fetch_query(query: str, limit: int, api_key: str) -> list[dict]:
    rows = []
    seen_ids = set()
    start_index = 0
    while start_index < limit:
        page = get_page(query, start_index, api_key)
        items = page.get("items") or []
        if not items:
            break

        for volume in items:
            volume_id = volume.get("id")
            if volume_id and volume_id not in seen_ids:
                seen_ids.add(volume_id)
                rows.append(volume_to_row(volume))

        start_index += len(items)
        if start_index >= page.get("totalItems", 0):
            break
        if start_index < limit:
            time.sleep(0.1)

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Google Books metadata for one or more search queries. "
            "Results are API records, not a complete catalogue."
        )
    )
    parser.add_argument(
        "--query",
        action="append",
        required=True,
        help="Google Books query; repeat this option for multiple queries.",
    )
    parser.add_argument(
        "--limit-per-query",
        type=int,
        default=200,
        help="Maximum results to request per query (default: 200).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output CSV.",
    )
    args = parser.parse_args()
    if args.limit_per_query < 1:
        parser.error("--limit-per-query must be positive.")

    api_key = os.environ.get("GOOGLE_BOOKS_API_KEY", "").strip()
    rows = []
    seen_ids = set()
    for query in args.query:
        query_rows = fetch_query(query, args.limit_per_query, api_key)
        for row in query_rows:
            if row["google_id"] not in seen_ids:
                seen_ids.add(row["google_id"])
                rows.append(row)
        print(f"{query!r}: fetched {len(query_rows)} unique volumes")

    output_path = args.output.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} unique volumes to {output_path}")


if __name__ == "__main__":
    main()

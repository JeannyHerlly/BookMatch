"""Fetch Open Library Search API records into a CSV."""

import argparse
import csv
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SEARCH_URL = "https://openlibrary.org/search.json"
USER_AGENT = "BookMatch/1.0"
TIMEOUT_SECONDS = 30
SEARCH_FIELDS = (
    "key",
    "title",
    "author_name",
    "first_publish_year",
    "subject",
    "edition_key",
    "cover_i",
    "isbn",
)
OUTPUT_FIELDS = (
    "openlibrary_work_id",
    "title",
    "authors",
    "first_publish_year",
    "subjects",
    "edition_ids",
    "isbns",
    "cover_id",
    "description",
)


def request_json(url: str, user_agent: str) -> dict:
    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"Open Library returned HTTP {error.code}; reduce the request "
            "rate or check the endpoint and query."
        ) from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError("Could not retrieve Open Library API data.") from error


def extract_description(value) -> str:
    if isinstance(value, dict):
        value = value.get("value", "")
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value or "")


def fetch_description(work_id: str, user_agent: str) -> str:
    url = f"https://openlibrary.org{work_id}.json"
    payload = request_json(url, user_agent)
    return extract_description(payload.get("description"))


def fetch_query(
    query: str,
    limit: int,
    include_descriptions: bool,
    user_agent: str,
) -> list[dict]:
    params = {
        "q": query,
        "limit": limit,
        "fields": ",".join(SEARCH_FIELDS),
    }
    payload = request_json(f"{SEARCH_URL}?{urlencode(params)}", user_agent)
    rows = []
    for item in payload.get("docs", []):
        work_id = str(item.get("key", ""))
        description = ""
        if include_descriptions and work_id.startswith("/works/"):
            time.sleep(1)
            description = fetch_description(work_id, user_agent)

        rows.append(
            {
                "openlibrary_work_id": work_id,
                "title": item.get("title", ""),
                "authors": "; ".join(item.get("author_name") or []),
                "first_publish_year": item.get("first_publish_year", ""),
                "subjects": "; ".join(item.get("subject") or []),
                "edition_ids": "; ".join(item.get("edition_key") or []),
                "isbns": "; ".join(item.get("isbn") or []),
                "cover_id": item.get("cover_i", ""),
                "description": description,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Open Library Search API records for one or more title or "
            "author queries. This is a search helper, not a complete dump."
        )
    )
    parser.add_argument(
        "--query",
        action="append",
        required=True,
        help="Open Library search query; repeat for additional queries.",
    )
    parser.add_argument(
        "--limit-per-query",
        type=int,
        default=100,
        help="Maximum results per query, from 1 to 100 (default: 100).",
    )
    parser.add_argument(
        "--include-descriptions",
        action="store_true",
        help=(
            "Fetch each result's work record for descriptions. This makes "
            "additional requests and is rate-limited."
        ),
    )
    parser.add_argument(
        "--contact",
        default=os.environ.get("OPENLIBRARY_CONTACT", "").strip(),
        help=(
            "Optional contact email or project URL for the User-Agent. "
            "Can also be set with OPENLIBRARY_CONTACT."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output CSV.",
    )
    args = parser.parse_args()
    if not 1 <= args.limit_per_query <= 100:
        parser.error("--limit-per-query must be between 1 and 100.")

    user_agent = USER_AGENT
    if args.contact:
        user_agent += f" (contact: {args.contact})"

    rows_by_work = {}
    for query in args.query:
        rows = fetch_query(
            query,
            args.limit_per_query,
            args.include_descriptions,
            user_agent,
        )
        for row in rows:
            work_id = row["openlibrary_work_id"]
            if work_id:
                rows_by_work.setdefault(work_id, row)
        print(f"{query!r}: fetched {len(rows)} works")
        time.sleep(1)

    output_path = args.output.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows_by_work.values())
    print(f"Saved {len(rows_by_work)} unique works to {output_path}")


if __name__ == "__main__":
    main()

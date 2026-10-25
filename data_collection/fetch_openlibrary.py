# ============================================================
# WARNING
# ============================================================
# This script may take several hours to complete, depending
# on the dataset size and API response times.
#
# It sends requests to the Open Library API and includes delays
# to avoid making requests too frequently.
#
# Progress is saved periodically, so the script can resume
# after an interruption.

import json
import time
from pathlib import Path
import pandas as pd
import requests

PROJECT_DIR = Path(__file__).resolve().parent

# deduplicate the books dataset first
INPUT_FILE = r"C:\Users\LOQ\project_books\.venv\datas\processed_books_dataset.csv"
OUTPUT_FILE = "openlibrary_metadata.csv"

MAX_RETRIES = 3
REQUEST_DELAY = 1.0
SAVE_EVERY = 25
SEARCH_LIMIT = 10

BASE_URL = "https://openlibrary.org"

HEADERS = {
    "User-Agent": "BookRecommendationProject/1.0 (your-email@example.com)"
}

OUTPUT_COLUMNS = [
    "google_id",
    "title",
    "openlibrary_work_key",
    "openlibrary_description",
    "openlibrary_subjects",
    "match_method",
    "match_status",
]


def load_books():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}\n"
            "Check INPUT_FILE and your project folder.")
    
    df = pd.read_csv(
        INPUT_FILE,
        dtype={
            "google_id": "string",
            "isbn_10": "string",
            "isbn_13": "string",
        },
    )

    required_columns = [
        "google_id",
        "title",
        "authors",
        "isbn_10",
        "isbn_13",]

    missing = [
        column for column in required_columns
        if column not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df = df.dropna(subset=["google_id"]).copy()
    df["google_id"] = df["google_id"].astype("string").str.strip()
    df = df[df["google_id"] != ""]

    # Only one row per Google Books volume.
    df = df.drop_duplicates(
        subset=["google_id"],
        keep="first",
    )
    return df.reset_index(drop=True)


def clean_isbn(isbn):
    if pd.isna(isbn):
        return None

    isbn = str(isbn).strip()
    if isbn.endswith(".0"):
        isbn = isbn[:-2]

    isbn = isbn.replace("-", "").replace(" ", "")

    return isbn or None


def normalize_text(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.casefold().strip().split())


def parse_authors(value):
    if not isinstance(value, str) or not value.strip():
        return []
    value = value.strip()

    try:
        parsed = json.loads(value)

        if isinstance(parsed, list):
            return [
                str(author).strip()
                for author in parsed
                if str(author).strip()
            ]
    except (json.JSONDecodeError, TypeError):
        pass
    return [value]


def authors_match(google_authors, openlibrary_authors):
    google_names = {
        normalize_text(author)
        for author in parse_authors(google_authors)
        if normalize_text(author)}

    openlibrary_names = {
        normalize_text(author)
        for author in (openlibrary_authors or [])
        if normalize_text(author)}

    return bool(google_names & openlibrary_names)


def title_matches(google_title, openlibrary_title):
    google_title = normalize_text(google_title)
    openlibrary_title = normalize_text(openlibrary_title)

    if not google_title or not openlibrary_title:
        return False

    return google_title == openlibrary_title


SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def make_request(url, params=None):
    for attempt in range(MAX_RETRIES):
        try:
            response = SESSION.get(
                url,
                params=params,
                timeout=30,
            )

            if response.status_code == 200:
                return response

            if response.status_code == 404:
                return None

            if response.status_code in (
                429, 500, 502, 503, 504
            ):
                retry_after = response.headers.get("Retry-After")

                try:
                    wait = float(retry_after)
                except (TypeError, ValueError):
                    wait = 2 ** attempt

                print(
                    f"Temporary HTTP {response.status_code}; "
                    f"retrying in {wait:g}s "
                    f"({attempt + 1}/{MAX_RETRIES})"
                )

                time.sleep(wait)
                continue

            print(
                f"HTTP {response.status_code} for {response.url}"
            )
            return None

        except requests.exceptions.RequestException as error:
            wait = 2 ** attempt

            print(
                f"Request error: {error}. "
                f"Retrying in {wait}s "
                f"({attempt + 1}/{MAX_RETRIES})"
            )

            time.sleep(wait)

    return None


def get_work_from_isbn(isbn):
    isbn = clean_isbn(isbn)

    if not isbn:
        return None

    url = f"{BASE_URL}/isbn/{isbn}.json"
    response = make_request(url)

    if response is None:
        return None

    try:
        data = response.json()
    except ValueError:
        return None

    works = data.get("works", [])

    if not isinstance(works, list) or not works:
        return None

    work_key = works[0].get("key")

    if isinstance(work_key, str) and work_key.startswith("/works/"):
        return work_key

    return None


def search_openlibrary(title, authors=None):
    if not isinstance(title, str) or not title.strip():
        return []
    
    params = {
        "title": title.strip(),
        "limit": SEARCH_LIMIT,}

    author_list = parse_authors(authors)

    if author_list:
        params["author"] = author_list[0]

    response = make_request(
        f"{BASE_URL}/search.json",
        params=params,)
    
    if response is None:
        return []
    try:
        data = response.json()
    except ValueError:
        return []

    return data.get("docs", [])


def choose_search_result(google_title, google_authors, docs):
    title_author_matches = []
    title_only_matches = []

    for doc in docs:
        ol_title = doc.get("title", "")

        if not title_matches(google_title, ol_title):
            continue

        openlibrary_authors = doc.get("author_name", [])

        if authors_match(google_authors, openlibrary_authors):
            title_author_matches.append(doc)
        else:
            title_only_matches.append(doc)

    if title_author_matches:
        return title_author_matches[0], "title_author"

    if len(title_only_matches) == 1:
        return title_only_matches[0], "title_only"

    return None, "not_found"


def get_work(work_key):

    if not isinstance(work_key, str):
        return None

    if not work_key.startswith("/works/"):
        return None

    response = make_request(
        f"{BASE_URL}{work_key}.json")

    if response is None:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def extract_description(work_data):
    if not work_data:
        return None

    description = work_data.get("description")

    if isinstance(description, dict):
        return description.get("value")

    if isinstance(description, str):
        return description

    return None


def extract_subjects(work_data):
    if not work_data:
        return []
    
    subjects = work_data.get("subjects", [])
    return subjects if isinstance(subjects, list) else []


def get_openlibrary_data(row):
    title = row.get("title")
    authors = row.get("authors")

    result = {
        "google_id": str(row["google_id"]),
        "title": title,
        "openlibrary_work_key": None,
        "openlibrary_description": None,
        "openlibrary_subjects": None,
        "match_method": None,
        "match_status": None,
    }

    # First try ISBN-13, then ISBN-10.
    for isbn_column in ("isbn_13", "isbn_10"):
        isbn = clean_isbn(row.get(isbn_column))

        if not isbn:
            continue

        print(f'{title} -> trying {isbn_column}: {isbn}')

        work_key = get_work_from_isbn(isbn)

        if work_key:
            result["openlibrary_work_key"] = work_key
            result["match_method"] = isbn_column
            break

        time.sleep(REQUEST_DELAY)

    # Fall back to title + author search.
    if not result["openlibrary_work_key"]:
        print(f"{title} -> trying title and author search")

        docs = search_openlibrary(title, authors)
        selected, method = choose_search_result(
            title,
            authors,
            docs,
        )

        if selected:
            work_key = selected.get("key")
            if isinstance(work_key, str) and work_key.startswith("/works/"):
                result["openlibrary_work_key"] = work_key
                result["match_method"] = method
        time.sleep(REQUEST_DELAY)

    work_key = result["openlibrary_work_key"]

    if not work_key:
        result["match_method"] = result["match_method"] or "not_found"
        result["match_status"] = "not_found"
        return result

    print(f"{title} -> {work_key}")

    work_data = get_work(work_key)
    if work_data is None:
        result["match_status"] = "work_fetch_failed"
        return result

    description = extract_description(work_data)
    subjects = extract_subjects(work_data)

    result["openlibrary_description"] = description
    result["openlibrary_subjects"] = json.dumps(
        subjects,
        ensure_ascii=False,
    )
    result["match_status"] = "matched"
    return result


def load_existing_results():
    if not OUTPUT_FILE.exists():
        print("No previous progress found.")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    existing = pd.read_csv(
        OUTPUT_FILE,
        dtype={"google_id": "string"},
    )

    # Add missing columns if an older output file is used.
    for column in OUTPUT_COLUMNS:
        if column not in existing.columns:
            existing[column] = pd.NA

    existing = existing[OUTPUT_COLUMNS]

    print(f"Loaded {len(existing)} saved records.")

    return existing


def save_results(results_df):
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )


def main():
    books_df = load_books()
    results_df = load_existing_results()

    # Skip only successfully fetched records.
    # Previously failed records will be retried.
    if not results_df.empty:
        successful_ids = set(
            results_df.loc[
                results_df["match_status"].eq("matched"),
                "google_id",
            ].dropna().astype(str)
        )
    else:
        successful_ids = set()

    pending_results = []
    total = len(books_df)

    for i, (_, row) in enumerate(books_df.iterrows(), start=1):
        google_id = str(row["google_id"])

        if google_id in successful_ids:
            continue

        print(f"\n[{i}/{total}] Processing: {row['title']}")

        try:
            result = get_openlibrary_data(row)
        except Exception as error:
            print(f"Unexpected error for {row['title']}: {error}")

            result = {
                "google_id": google_id,
                "title": row["title"],
                "openlibrary_work_key": None,
                "openlibrary_description": None,
                "openlibrary_subjects": None,
                "match_method": "error",
                "match_status": "error",
            }

        pending_results.append(result)

        if len(pending_results) >= SAVE_EVERY:
            new_results = pd.DataFrame(
                pending_results,
                columns=OUTPUT_COLUMNS,
            )

            results_df = pd.concat(
                [results_df, new_results],
                ignore_index=True,
            )

            # Keep only the latest attempt per Google Books volume.
            results_df = results_df.drop_duplicates(
                subset=["google_id"],
                keep="last",
            )

            save_results(results_df)

            successful_ids.update(
                new_results.loc[
                    new_results["match_status"].eq("matched"),
                    "google_id",
                ].dropna().astype(str)
            )

            pending_results = []

            print(f"Progress saved: {len(results_df)} records")

        time.sleep(REQUEST_DELAY)

    # Save any remaining results.
    if pending_results:
        new_results = pd.DataFrame(
            pending_results,
            columns=OUTPUT_COLUMNS,
        )

        results_df = pd.concat(
            [results_df, new_results],
            ignore_index=True,
        )

        results_df = results_df.drop_duplicates(
            subset=["google_id"],
            keep="last",
        )

    save_results(results_df)

    print("\nEnrichment complete.")
    print("Input books:", total)
    print("Saved metadata records:", len(results_df))
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

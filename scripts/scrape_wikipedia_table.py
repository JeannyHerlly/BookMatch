"""Export a selected table from an English Wikipedia article to CSV."""

import argparse
from io import StringIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pandas as pd


USER_AGENT = "BookMatchResearch/1.0 (Wikipedia table extraction)"
TIMEOUT_SECONDS = 30


def is_wikipedia_host(hostname: str | None) -> bool:
    return hostname == "wikipedia.org" or bool(
        hostname and hostname.endswith(".wikipedia.org")
    )


def fetch_article(url: str) -> str:
    parsed_url = urlparse(url)
    if (
        parsed_url.scheme != "https"
        or not is_wikipedia_host(parsed_url.hostname)
    ):
        raise ValueError("URL must be an HTTPS Wikipedia article.")

    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            final_url = urlparse(response.geturl())
            if not is_wikipedia_host(final_url.hostname):
                raise ValueError("Wikipedia redirected to an unexpected host.")
            return response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Could not fetch the Wikipedia article (HTTP/network error: "
            f"{getattr(error, 'code', 'unavailable')})."
        ) from error


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download HTML tables from an English Wikipedia article and "
            "export one table as CSV."
        )
    )
    parser.add_argument(
        "--url",
        required=True,
        help="HTTPS URL of the Wikipedia article containing the table.",
    )
    parser.add_argument(
        "--table-index",
        type=int,
        default=0,
        help="Zero-based table index returned by pandas (default: 0).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to the output CSV.",
    )
    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="Print table indexes and headers without writing a CSV.",
    )
    args = parser.parse_args()

    html = fetch_article(args.url)
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError as error:
        raise RuntimeError("No readable HTML tables were found.") from error

    if not tables:
        raise RuntimeError("No readable HTML tables were found.")

    if args.list_tables:
        for index, table in enumerate(tables):
            print(f"{index}: {', '.join(map(str, table.columns))}")
        return

    if args.output is None:
        parser.error("--output is required unless --list-tables is used.")

    if not 0 <= args.table_index < len(tables):
        raise ValueError(
            f"Table index {args.table_index} is out of range; "
            f"the article has {len(tables)} readable tables."
        )

    output_path = args.output.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tables[args.table_index].to_csv(output_path, index=False)
    print(
        f"Saved table {args.table_index} ({len(tables[args.table_index])} "
        f"rows) to {output_path}"
    )


if __name__ == "__main__":
    main()

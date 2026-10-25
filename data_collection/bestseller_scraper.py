"""Export a selected table from an English Wikipedia article to CSV."""

from pathlib import Path
from bs4 import BeautifulSoup
import requests
import pandas as pd


url = "https://en.wikipedia.org/wiki/List_of_best-selling_books"
headers = {
    "User-Agent": "BookRecommendationProject/1.0 (MY_GMAIL)"
}
page = requests.get(url, headers=headers)
print(page.status_code)
soup = BeautifulSoup(page.text, "html.parser")


if page.status_code == 200:

    # Find all Wikipedia tables
    tables = soup.select("table.wikitable")
    print("Number of tables found:", len(tables))

    for i, table in enumerate(tables, start=1):
        header_row = table.select_one("tr")

        if not header_row:
            continue

        headers = [
            cell.get_text(" ", strip=True)
            for cell in header_row.select("th, td")]

        books = []

        # Extract all rows in this table
        for row in table.select("tr")[1:]:
            cells = row.select("th, td")

            values = [
                cell.get_text(" ", strip=True)
                for cell in cells]

            if len(values) == len(headers):
                books.append(values)

        # Convert table to a df
        df = pd.DataFrame(books, columns=headers)

        # Save each table separately
        output_dir = Path.cwd() / ".venv" / "datas" / "data_collection" / "bestsellers"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = output_dir / f"books_table_{i}.csv"
        df.to_csv(
            filename,
            index=False,
            encoding="utf-8-sig")

        print(f"Saved {filename}: {len(df)} rows")

else:
    print("Failed to load webpage:", page.status_code)


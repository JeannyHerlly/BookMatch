
import time
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://en.wikipedia.org"
CATEGORY_URL = f"{BASE_URL}/wiki/Category:Books_by_award"

HEADERS = {
    # Replace with a valid contact address for your project.
    "User-Agent": "BookRecommendationProject/1.0 (your-email@example.com)"
}

WANTED_AWARDS = [
    "Booker Prize–winning works",
    "Carnegie Medal in Literature–winning works",
    "S.E.A. Write Award–winning works",
    "International Booker Prize–winning works",
    "Michael L. Printz Award–winning works",
    "Women's Prize for Fiction–winning works",
    "Pulitzer Prize",
    "National Book Award winners",
    "Akutagawa",
    "British Book Award–winning works",
]


def get_soup(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_award_categories():
    soup = get_soup(CATEGORY_URL)
    award_links = []

    for a in soup.select("div.mw-category a"):
        href = a.get("href")
        title = a.get_text(strip=True)

        if href and href.startswith("/wiki/Category:"):
            if any(name.casefold() in title.casefold()
                   for name in WANTED_AWARDS):
                award_links.append({
                    "award": title,
                    "url": BASE_URL + href
                })
    return award_links


def get_books_from_category(url):
    """Collect book titles listed on a category page."""
    soup = get_soup(url)

    books = [
        a.get_text(strip=True)
        for a in soup.select("div.mw-category a")
        if a.get("href")
        and not a.get("href").startswith("/wiki/Category:")
    ]
    return books


def main():
    selected_awards = get_award_categories()

    print(f"Selected award categories: {len(selected_awards)}")

    all_records = []
    for award in selected_awards:
        try:
            books = get_books_from_category(award["url"])
            for book in books:
                all_records.append({
                    "award": award["award"],
                    "book": book
                })
            print(f'{award["award"]}: {len(books)} titles')

        except requests.RequestException as error:
            print(f'Failed: {award["award"]}: {error}')

        time.sleep(random.uniform(1, 2))

    award_books = pd.DataFrame(
        all_records,
        columns=["award", "book"])

    award_books = award_books.drop_duplicates()

    output_file = "books_by_award.csv"
    award_books.to_csv(output_file, index=False)

    print(f"Saved {len(award_books)} award records to {output_file}")


if __name__ == "__main__":
    main()

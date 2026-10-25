"""Fetch book metadata from the Google Books volumes API into a CSV."""
import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
print("API key loaded:", API_KEY is not None)
url = "https://www.googleapis.com/books/v1/volumes"
output_file = "books_dataset.csv"


if os.path.exists(output_file):
    books_df = pd.read_csv(output_file)
    all_books = books_df.to_dict("records")
else:
    all_books = []

existing_ids = {
    book["google_id"]
    for book in all_books
    if pd.notna(book.get("google_id"))
}
print("Existing books:", len(all_books))


def get_isbn(volume_info):
    isbn_10 = None
    isbn_13 = None
    for identifier in volume_info.get("industryIdentifiers", []):
        if identifier.get("type") == "ISBN_10":
            isbn_10 = identifier.get("identifier")
        elif identifier.get("type") == "ISBN_13":
            isbn_13 = identifier.get("identifier")

    return isbn_10, isbn_13


def extract_book(item, search_type):
    volume_info = item.get("volumeInfo", {})
    isbn_10, isbn_13 = get_isbn(volume_info)

    return {
        "google_id": item.get("id"),
        "title": volume_info.get("title"),
        "subtitle": volume_info.get("subtitle"),
        "authors": ", ".join(volume_info.get("authors", [])),
        "publisher": volume_info.get("publisher"),
        "published_date": volume_info.get("publishedDate"),
        "description": volume_info.get("description"),
        "categories": ", ".join(volume_info.get("categories", [])),
        "average_rating": volume_info.get("averageRating"),
        "ratings_count": volume_info.get("ratingsCount"),
        "page_count": volume_info.get("pageCount"),
        "language": volume_info.get("language"),
        "isbn_10": isbn_10,
        "isbn_13": isbn_13,
        "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail"),
        "search_category": search_type
    }


def search_books(query, max_results=40):
    params = {
        "q": query,
        "langRestrict": "en",
        "maxResults": max_results,
        "key": API_KEY
        }
    response = requests.get(
        url,
        params=params,
        timeout=30)

    if response.status_code == 200:
        data = response.json()
        return data.get("items", [])
    
    elif response.status_code == 429:
        print("Quota exceeded.")
        return []
    
    else:
        print("API error:", response.status_code)
        print(response.text)
        return []


def add_books(items, search_type):
    new_books = 0
    for item in items:
        google_id = item.get("id")
        if google_id and google_id not in existing_ids:
            book = extract_book(
                item,
                search_type
            )
            all_books.append(book)
            existing_ids.add(google_id)
            new_books += 1
    return new_books

categories = [
    "fiction",
    "fantasy",
    "science fiction",
    "mystery",
    "thriller",
    "romance",
    "horror",
    "adventure",
    "classic literature",
    "historical fiction",
    "young adult",
    "children's books",
    "manga",
    "comics",
    "graphic novels",
    "biography",
    "history",
    "philosophy",
    "psychology",
    "science"
]


for category in categories:
    print("\nSearching:", category)
    items = search_books(
        f"subject:{category}"
    )
    new_books = add_books(
        items,
        category
    )
    print("New books:", new_books)

    # Save after every category
    pd.DataFrame(all_books).to_csv(
        output_file,
        index=False
    )
    time.sleep(1)
print("\nFinished!")
print("Total books:", len(all_books))


#Curated list of well known books
anchor = pd.read_csv(r"C:\\Users\\LOQ\\project_books\\.venv\\datas\\books_anchor.csv")

for each_book in anchor["Title"].dropna():
    print("\nSearching:", each_book)
    items = search_books(
        f'intitle:"{each_book}"',
        max_results=10
        )
    new_books = add_books(
        items,
        "specific_title")

    print("New books:", new_books)

    pd.DataFrame(all_books).to_csv(
        output_file,
        index=False)

    time.sleep(1)

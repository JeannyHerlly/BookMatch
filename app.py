from flask import Flask, request, jsonify, render_template
import pandas as pd
import sqlite3
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
DB_PATH = DATA_DIR / "bookmatch.db"

from sbert import (recommend_books, recommend_from_likes, processed_books)


def books_to_json(df):

    columns = [
        "google_id",
        "google_books_url",
        "title",
        "authors",
        "categories",
        "description",
        "thumbnail",
        "published_date",
        "is_award_winner",
        "award_names",
        "is_bestseller",
        "similarity",
        "final_score",
    ]


    # Return only fields needed by the frontend.
    safe_columns = [
        column for column in columns
        if column in df.columns
    ]

    return df[safe_columns].fillna("").to_dict(orient="records")


app = Flask(__name__)

DATA_DIR.mkdir(parents=True, exist_ok=True)

with sqlite3.connect(DB_PATH) as connection:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS liked_books (
            google_id TEXT PRIMARY KEY,
            liked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/healthz")
def health_check():
    return jsonify({"status": "ok"})


@app.route("/api/search")
def search():
    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify([])

    matches = processed_books[
        processed_books["title_clean"].fillna("").str.contains(
            query, regex=False
        )
        |
        processed_books["author_clean"].fillna("").str.contains(
            query, regex=False
        )
    ]

    return jsonify(
        matches[
            [
                "google_id",
                "title",
                "authors",
                "categories",
                "published_date",
                "description",
                "thumbnail",
                "is_award_winner",
                "award_names",
                "is_bestseller"
            ]
        ].fillna("").to_dict(orient="records")
    )


@app.route("/api/discover")
def discover():
    count = int(request.args.get("count", 20))
    category = request.args.get("category", "All").strip()

    books = processed_books.copy()

    if category.lower() == "bestseller":
        books = books[
            books["is_bestseller"]
            .fillna(False)
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        ]

    elif category.lower() in {"award winner", "award winners"}:
        books = books[
            books["is_award_winner"]
            .fillna(False)
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        ]

    elif category.lower() != "all":
        books = books[
            books["category_clean"]
            .fillna("")
            .astype(str)
            .str.contains(category, case=False, regex=False)
        ]

    if books.empty:
        return jsonify([])

    if len(books) > count:
        books = books.sample(n=count)

    columns = [
        "google_id", "title", "authors", "categories",
        "description", "thumbnail", "published_date",
        "is_award_winner", "award_names", "is_bestseller"
    ]

    return jsonify(
        books[columns].fillna("").to_dict(orient="records")
    )
    



@app.route("/api/likes", methods=["GET"])
def get_liked_books():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT google_id
            FROM liked_books
            ORDER BY liked_at DESC
        """).fetchall()

    liked_ids = [str(row[0]) for row in rows]

    # Retrieve complete book records from the existing dataset.
    books = processed_books[
        processed_books["google_id"].astype(str).isin(liked_ids)
    ].copy()

    # Preserve the order in which books were liked.
    books["__like_order"] = books["google_id"].astype(str).map(
        {google_id: i for i, google_id in enumerate(liked_ids)}
    )
    books = books.sort_values("__like_order").drop(
        columns="__like_order"
    )

    books = books.fillna("")

    # Convert any sets in the book records into lists
    records = books.to_dict(orient="records")

    for record in records:
        for key, value in record.items():
            if isinstance(value, set):
                record[key] = list(value)

    return jsonify(records)



@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True) or {}

    title = data.get("title")
    author = data.get("author")

    try:
        results = recommend_books(title, author=author, n=10)

        # Replace missing pandas/NumPy values with None
        # so Flask can serialize them as JSON null.
        results = results.astype(object).where(
            pd.notna(results), None
        )

        return jsonify(results.to_dict(orient="records"))

    except Exception as e:
        app.logger.exception("Recommendation endpoint failed")
        return jsonify({"error": str(e)}), 500




@app.route("/api/likes", methods=["POST"])
def add_liked_book():
    data = request.get_json(silent=True) or {}
    google_id = str(data.get("google_id", "")).strip()

    if not google_id:
        return jsonify({"error": "Missing google_id"}), 400

    # Only allow books that exist in the dataset.
    exists = (
        processed_books["google_id"].astype(str) == google_id
    ).any()

    if not exists:
        return jsonify({"error": "Book not found"}), 404

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO liked_books (google_id)
            VALUES (?)
        """, (google_id,))

    return jsonify({
        "success": True,
        "google_id": google_id
    })


@app.route("/api/likes/<google_id>", methods=["DELETE"])
def remove_liked_book(google_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            DELETE FROM liked_books
            WHERE google_id = ?
        """, (google_id,))

    return jsonify({
        "success": True,
        "google_id": google_id
    })


@app.route("/api/recommendations/personalized")
def personalized_recommendations():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT google_id
            FROM liked_books
            ORDER BY liked_at DESC
        """).fetchall()

    liked_ids = [row[0] for row in rows]

    if not liked_ids:
        return jsonify([])

    results = recommend_from_likes(liked_ids, n=10)

    return jsonify(books_to_json(results))



def get_google_books_url(google_id):
    """Return the Google Books page URL for a book."""
    if google_id is None:
        return None

    google_id = str(google_id).strip()

    if not google_id or google_id.lower() in {"nan", "none", "null"}:
        return None

    from urllib.parse import quote
    return f"https://books.google.com/books?id={quote(google_id, safe='')}"


if __name__ == "__main__":
    app.run(debug=True)

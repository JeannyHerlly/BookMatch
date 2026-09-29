from flask import Flask, request, jsonify, render_template
import pandas as pd

from sbert import recommend_books, processed_books

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

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
            "thumbnail"
            ]
        ].fillna("").to_dict(orient="records")
    )

@app.route("/api/discover")
def discover():
    count = int(request.args.get("count", 5))
    category = request.args.get("category", "").strip().lower()

    books = processed_books.copy()

    if category and category != "all":
        category_mask = (
            books["category_clean"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(category, regex=False)
        )

        books = books[category_mask]

    if books.empty:
        return jsonify([])

    if len(books) > count:
        books = books.sample(n=count)

    return jsonify(
        books[
            [
                "google_id",
                "title",
                "authors",
                "categories",
                "description",
                "thumbnail"
            ]
        ]
        .fillna("")
        .to_dict(orient="records")
    )


@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json()

    title = data.get("title")
    author = data.get("author")

    results = recommend_books(
        title,
        author=author,
        n=10
    )

    results = results.fillna("")
    return jsonify(results.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)

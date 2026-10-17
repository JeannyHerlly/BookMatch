# Book Recommender

A book discovery app built with Flask. Search and filter a book catalogue, save
liked books, and get recommendations based on book descriptions, categories,
titles, and authors.

## Features

- Search books by title or author.
- Browse the catalogue by genre, bestseller status, and award recognition.
- Get recommendations for a selected book or based on saved likes.
- Save and remove liked books in a local SQLite database.
- Responsive book cards and detail pages.

## Project structure

```text
app.py                         Flask routes and likes API
sbert.py                       Dataset loading, embeddings, and ranking
static/                        Frontend JavaScript and CSS
templates/                     Flask HTML template
notebooks/
  data_processing.ipynb        Clean and prepare the core book catalogue
  bestseller_awardwinner.ipynb Match bestseller and award records
data/                          Local input and generated files (not committed)
```

## Setup

Use Python 3.10 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-notebooks.txt
```

The first run of `sbert.py` downloads the `all-MiniLM-L6-v2` model through
Sentence Transformers. An internet connection is needed for that initial
download.

## Data and processing

Datasets and SQLite databases are intentionally excluded from this repository.
They can be subject to third-party licenses and terms, and should not be
redistributed without permission. Obtain the required source files from their
respective providers and review their terms before use.

Create a `data/` directory and provide the input files expected by the
notebooks:

- `books_dataset.csv` — source catalogue with the book fields used in
  `notebooks/data_processing.ipynb`.
- `books.db` — award tables used by the processing notebook.
- `books_by_award.csv`, `award_matches.csv`, and CSV exports in `bestsellers/`
  — award and bestseller matching inputs used by
  `notebooks/bestseller_awardwinner.ipynb`.

Run the notebooks from the `notebooks/` directory. They use relative paths into
`data/` and have had saved cell outputs removed. The processing notebook
produces `data/processed_books_dataset.csv`; the enrichment notebook produces
the final catalogue:

```text
data/processed_books_with_bestsellers.csv
```

Before running the app, confirm the final CSV includes the columns used by
`sbert.py`, including `google_id`, `title`, `authors`, `categories`,
`description`, `author_set`, `title_clean`, `category_clean`,
`is_award_winner`, `award_names`, and `is_bestseller`.

The notebooks preserve the project’s data preparation and matching workflow.
Award matching uses manually verified relationships in `award_matches.csv`;
review those matches when replacing or updating source data. The award database
must contain the `awards` and `book_awards` tables before running the award join
in the processing notebook.

## Run the app

From the repository root, with the processed dataset in place:

```powershell
python app.py
```

Then open <http://127.0.0.1:5000>.

## Recommendation approach

The recommender precomputes normalized sentence embeddings for titles,
categories, and descriptions with `all-MiniLM-L6-v2`. Its ranking combines
cosine similarity with small bonuses for shared authors, award winners, and
bestsellers. Recommendations for liked books use the strongest similarity to
any saved book and a small award bonus.

## Notes

- Likes are stored in the local `bookmatch.db`; the database is not committed.
- Generated datasets, model files, and Python caches are not committed.
- No personal book data should be added to the public repository.

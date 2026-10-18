---
title: BookMatch - Book Recommender
sdk: docker
app_port: 7860
---

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

- `books_enriched.csv` — enriched source catalogue with the book fields used in
  `notebooks/data_processing.ipynb`.
- `books.db` — award tables used by
  `notebooks/bestseller_awardwinner.ipynb`.
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
`description`, `author_set`, `title_clean`, `author_clean`, `category_clean`,
`clean_description`, `is_award_winner`, `award_names`, and `is_bestseller`.

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

## Free public demo on Render

The repository includes a free Render Blueprint in `render.yaml`. Render Free
services sleep after inactivity, use ephemeral storage, and have limited memory.
The app downloads its dataset and sentence-transformer model at startup, so
initial startup and wake-ups may take several minutes. Likes can be lost when
the service restarts or redeploys. Render's free limits can change; review its
current pricing and resource limits before deploying.

1. Confirm you have permission to publicly serve the processed catalogue.
2. In Render, create a Blueprint from this repository and set:
   - `BOOK_DATA_URL` to the direct HTTPS URL for the processed CSV.
   - `BOOK_DATA_TOKEN` to a Hugging Face read token (keep it secret).
   - `BOOK_DATA_SHA256` optionally, to verify the downloaded file.
3. Deploy the Blueprint and share the public `onrender.com` URL with visitors.
   Do not share the local `127.0.0.1` address.

`BOOK_DATA_URL` should point directly to the CSV bytes, not to a preview or
login page. The downloader requires HTTPS, validates the expected CSV columns,
and never includes the configured token in its error message.

Render's free services do not include persistent disks. The service uses
temporary storage for the catalogue, downloaded model, and likes database.
Search engines are asked not to index the site, but this is only a
discoverability hint: anyone with the URL can visit and share it. This is not
password protection.

## Hugging Face Spaces alternative

Hugging Face Spaces can also run this Docker app, but free Docker CPU hosting
may require a paid PRO subscription. Check current account eligibility and
pricing before creating a Space.

1. Create a **public Space** and choose **Docker** as its SDK.
2. Add a Space secret named `HF_TOKEN` with a read token that has access to the
   private dataset.
3. Add a Space variable named `BOOK_DATA_URL` with the direct CSV URL:

   ```text
   https://huggingface.co/datasets/Jeanny26/processed_books_with_bestsellers.csv/resolve/main/processed_books_with_bestseller_award.csv?download=true
   ```

4. Optionally set `BOOK_DATA_SHA256` to verify the file contents.
5. Push this repository's `main` branch to the Space's Git remote. The Space
   builds the Docker image and starts the app on port 7860.

For the Space's Git remote, follow the repository-specific URL shown on its
page; it will look like `https://huggingface.co/spaces/USERNAME/SPACE_NAME`.
Keep `HF_TOKEN` in Space settings only. Visitors use the public Space URL; they
do not need access to the private dataset repository. The app serves catalogue
records through its public API, so only use a dataset you are permitted to
redistribute through the demo.

The app asks search engines not to index its pages, but this is only a
discoverability hint. Hugging Face public Spaces can still be listed on
Hugging Face, and anyone who gets the URL can visit it or share it. This is not
password protection or a way to restrict access to invited people, and it does
not change whether you have permission to display the dataset. For actual
access control, use a private Space; viewers will need authorized Hugging Face
accounts.

The Space filesystem may not persist across rebuilds or resets. Likes can be
lost, and a sleeping Space can make the first visit slow.

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

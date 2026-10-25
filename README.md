# BookMatch — Book Recommendation System

BookMatch is a Flask web application that helps readers discover books using semantic similarity, book metadata, and award/bestseller information. It demonstrates an end-to-end data science workflow, from data collection and preparation to recommendation ranking and web application development.

**[Try the Live Demo](https://jeannyherlly.pythonanywhere.com/)**

## Features

- Search books by title or author.
- Browse books by genre, bestseller status, and award recognition.
- Get recommendations based on book content and saved likes.
- Save and remove liked books.

## Recommendation System

BookMatch uses **Sentence-BERT (`all-MiniLM-L6-v2`)** to generate embeddings from book titles, categories, and descriptions. Cosine similarity measures how closely books are related and serves as the primary basis for recommendation relevance.

The ranking incorporates additional signals:

- **Content similarity:** The main determinant of relevance.
- **Author matching:** Handled separately to account for books with multiple authors and provide an additional bonus when authors match.
- **Award-winning status:** Adds a ranking bonus rather than determining relevance on its own.
- **Bestseller status:** Adds a ranking bonus rather than determining relevance on its own.

For recommendations based on saved likes, the system considers the strongest similarity to any liked book and incorporates an award bonus.

**Grid search** tests different weight combinations to identify the best-performing configuration according to the selected evaluation metric.

## Data Collection and Preparation

Datasets and SQLite databases are intentionally excluded from this repository. They can be subject to third-party licenses and terms, and should not be redistributed without permission. Obtain the required source files from their respective providers and review their terms before use.

BookMatch combines data from multiple sources:
•	**Google Books API**: Book metadata, descriptions, categories, ratings, and cover thumbnails.
•	**Open Library:** Supplementary descriptions and subjects/categories.
•	**Wikipedia:** Bestseller lists and award-related book lists.

The data pipeline includes exploratory analysis, data cleaning, metadata enrichment, and matching books against award and bestseller lists. Award matches are manually reviewed before being incorporated into the final dataset.

## Project Structure

```text
app.py                         Flask routes and likes API
sbert.py                       Dataset loading, embeddings, and ranking
static/                        Frontend JavaScript and CSS
templates/                     Flask HTML template
scripts/
  fetch_google_books.py        Fetch Google Books volume metadata
  fetch_openlibrary.py         Fetch Open Library work/search metadata
  scrape_wikipedia_table.py    Export a Wikipedia article table to CSV
notebooks/
  data_processing.ipynb        Clean and prepare the core book catalogue
  bestseller_awardwinner.ipynb Match bestseller and award records
data/                          Local input and generated files (not committed)
```

## Limitations

- **Incomplete metadata:** Some books have missing descriptions, categories, or other information, limiting the details available for comparison.
- **Metadata quality:** Some records contain generic, irrelevant, or insufficiently descriptive information, making it harder to distinguish books with similar categories but different themes.
- **Duplicate records:** Some duplicates may remain because differences in titles, editions, ISBNs, or incomplete metadata make them difficult to identify reliably.
- **Open Library coverage:** Some books could not be matched to Open Library records. Enrichment was also time-consuming, limiting the number of books that could be supplemented.
- **Limited personalization:** Recommendations rely mainly on book content and saved likes rather than learning from a large dataset of user ratings or reading histories.
- **Ranking limitations:** Similarity and award/bestseller bonuses do not guarantee relevance. Results depend on metadata quality, label accuracy, and ranking weights.
- **Grid search limitations:** Weight optimization uses predefined test books and manually identified relevant books. Relevant recommendations absent from these reference lists are not counted as relevant. Using only a few test books per case may also bias the selected weights toward those books, limiting generalizability to the full catalogue.

### Future Improvements

- Improve metadata matching and duplicate detection.
- Expand and diversify the recommendation evaluation set.
- Evaluate recommendations using more comprehensive relevance judgments.
- Incorporate user feedback to improve personalization.

## Run Locally

### Requirements

- Python 3.10 or newer
- The processed dataset expected by `sbert.py`

### Installation

Create and activate a virtual environment, then install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

To work with the data-processing notebooks, also install:

```powershell
python -m pip install -r requirements-notebooks.txt
```

The first run downloads the `all-MiniLM-L6-v2` model through Sentence Transformers and requires an internet connection.

### Start the Application

Ensure the required processed dataset is available, then run:

```powershell
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

**Note:** The datasets and SQLite databases required to reproduce the full workflow are not included in the repository.

## Deployment

The public demo is hosted on [PythonAnywhere](https://jeannyherlly.pythonanywhere.com/). The hosted version uses a separate deployment bundle with a precomputed similarity matrix.

Docker and Render configuration files are also included for alternative deployments. Availability and resource limits depend on each hosting platform's current plan.

## Data Sources and Attribution

- [Google Books API documentation](https://developers.google.com/books/docs/v1/using)
- [Open Library API documentation](https://openlibrary.org/developers/api)
- [Wikipedia licensing information](https://en.wikipedia.org/wiki/Wikipedia:Copyrights)

Review the applicable terms before redistributing collected data. Keep API keys, `.env`, `.venv/`, generated datasets, and local databases out of version control.

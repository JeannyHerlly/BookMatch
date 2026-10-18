from sentence_transformers import SentenceTransformer
import ast  
import pandas as pd
import numpy as np

# Load processed dataset
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
DATA_PATH = DATA_DIR / "processed_books_with_bestsellers.csv"

processed_books = pd.read_csv(DATA_PATH)

for target_column, candidates in {
    "categories_clean": (
        "category_clean",
        "categories_final",
        "search_category",
        "openlibrary_categories",
        "categories",
    ),
    "clean_description": (
        "description_final",
        "description",
        "openlibrary_description",
    ),
}.items():
    if target_column not in processed_books:
        source_column = next(
            (column for column in candidates if column in processed_books),
            None,
        )
        if source_column is None:
            raise ValueError(
                f"The processed book dataset is missing {target_column!r} "
                f"and its supported alternatives: {', '.join(candidates)}."
            )
        processed_books[target_column] = processed_books[source_column]

for target_column, source_column in {
    "categories": "categories_clean",
    "description": "clean_description",
}.items():
    if target_column not in processed_books:
        processed_books[target_column] = processed_books[source_column]

# Load SBERT model ONCE
model = SentenceTransformer("all-MiniLM-L6-v2")

processed_books["author_set"] = processed_books["author_set"].apply(
    ast.literal_eval
)

description_text = processed_books["clean_description"].fillna("").astype(str)
category_text = processed_books["categories_clean"].fillna("").astype(str)

has_desc = description_text.str.strip().str.len() > 6
has_cat = category_text.str.strip().str.len() > 0

# Encode only non-empty values; use a zero vector for missing
def encode_masked(series, mask):
    emb = np.zeros((len(series), 384), dtype=np.float32)
    if mask.any():
        emb[mask.values] = model.encode(
            series[mask].tolist(),
            normalize_embeddings=True,
            batch_size=64,
            show_progress_bar=True
        )
    return emb

title_embeddings = encode_masked(processed_books['title'].fillna(''), processed_books['title'].notna())
category_embeddings = encode_masked(category_text, has_cat)
description_embeddings = encode_masked(description_text, has_desc)

from sklearn.metrics.pairwise import cosine_similarity
title_similarity = cosine_similarity(title_embeddings)

category_similarity = cosine_similarity(category_embeddings)

description_similarity = cosine_similarity(description_embeddings)

title_weight = 0.525
category_weight = 0.05
description_weight = 0.425

final_similarity = (
    title_weight * title_similarity +
    category_weight * category_similarity +
    description_weight * description_similarity
)


from rapidfuzz import fuzz

def authors_match(selected_authors, candidate_authors):

    for selected_author in selected_authors:
        for candidate_author in candidate_authors:

            score = fuzz.token_set_ratio(
                selected_author,
                candidate_author
            )

            if score >= 50:
                return True

    return False

def is_same_book(book_idx, selected_idx):

    selected_title = processed_books.loc[
        selected_idx, "title_clean"]
    
    candidate_title = processed_books.loc[
        book_idx, "title_clean"]
    
    selected_authors = processed_books.loc[
        selected_idx, "author_set"]
    
    candidate_authors = processed_books.loc[
        book_idx, "author_set"]

    # Check authors
    if not authors_match(selected_authors, candidate_authors):
        return False

    # Check titles
    title_score = fuzz.token_set_ratio(selected_title, candidate_title)

    return title_score >= 85

indices = pd.Series(processed_books.index, index=processed_books["title_clean"]).drop_duplicates()

import re
import unicodedata
def clean_title(title):
    title = unicodedata.normalize("NFKD", title)     # Remove accents
    title = title.encode("ascii", "ignore").decode("ascii")
    title = str(title).lower() 
    title = re.sub(r"\([^)]*\)", "", title)     # Remove text in parentheses
    title = re.sub(r"[^a-z0-9\s]", " ", title)     # Remove punctuation
    title = re.sub(r"\s+", " ", title).strip()     # Normalize spaces
    return title

def clean_author(author):
    author = str(author)
    author = unicodedata.normalize("NFKC", author)
    author = author.lower()
    # Keep Unicode letters/numbers, remove punctuation
    author = re.sub(r"[^\w\s]", "", author, flags=re.UNICODE)
    author = " ".join(author.split())
    return author


AUTHOR_BONUS = 0.1
AWARD_BONUS = 0.02
BESTSELLER_BONUS = 0.02

def recommend_books(title, author=None, n=10):
    title_clean = clean_title(title)

    if title_clean not in indices:
        print("Book not found.")
        return pd.DataFrame()

    idc = indices[title_clean]

    if isinstance(idc, pd.Series):
        candidate_indices = [int(x) for x in idc.values]
    else:
        candidate_indices = [int(idc)]

    # If an author was provided, narrow the candidates to that author
    if author is not None and len(candidate_indices) > 1:
        author_clean = clean_author(author)

        author_matches = [
            idx for idx in candidate_indices
            if author_clean in processed_books.loc[idx, "author_set"]
        ]

        if author_matches:
            candidate_indices = author_matches

    # Select the query book
    idx = candidate_indices[0]

    target_authors = processed_books.loc[idx, "author_set"]

    similarity_scores = list(
        enumerate(final_similarity[idx])
    )

    recommendations = []

    for book_idx, similarity in similarity_scores:

        if book_idx == idx:
            continue

        same_book = is_same_book(idx, book_idx)

        if same_book:
            continue

        candidate_authors = processed_books.loc[book_idx, "author_set"]

        same_author = bool(target_authors & candidate_authors)

        author_bonus = AUTHOR_BONUS if same_author else 0

        candidate_book = processed_books.iloc[book_idx]

        is_award_winner = candidate_book["is_award_winner"]
        is_bestseller = candidate_book["is_bestseller"]

        award_bonus = (AWARD_BONUS if is_award_winner else 0.0)
        bestseller_bonus = (BESTSELLER_BONUS if is_bestseller else 0.0)


        final_score = similarity + author_bonus + award_bonus + bestseller_bonus

        recommendations.append({
            "index": book_idx,
            "similarity": similarity,
            "author_bonus": author_bonus,
            "final_score": final_score,
            "same_book": same_book,
            "award_winning": is_award_winner,
            "award_books": candidate_book["award_names"],
            "bestseller": is_bestseller
        })

    recommendations.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    recommendations = recommendations[:n]

    book_indices = [
        x["index"] for x in recommendations
    ]

    results = processed_books.iloc[book_indices][
        ["title", "authors", "categories","description"]
    ].copy()

    results["similarity"] = [
        x["similarity"] for x in recommendations
    ]

    results["author_bonus"] = [
        x["author_bonus"] for x in recommendations
    ]

    results["final_score"] = [
        x["final_score"] for x in recommendations
    ]

    results["same_book"] = [
        x["same_book"] for x in recommendations
    ]

    results["award_winning"] = [
        x["award_winning"] for x in recommendations
    ]

    results["award_books"] = [
        x["award_books"] for x in recommendations
    ]

    results["bestseller"] = [
        x["bestseller"] for x in recommendations
    ]

    return results


def recommend_from_likes(liked_google_ids, n=10):
    if not liked_google_ids:
        return pd.DataFrame()

    # Find the dataset positions of books the user liked.
    liked_positions = [
        i
        for i, google_id in enumerate(
            processed_books["google_id"].fillna("").astype(str)
        )
        if google_id in set(liked_google_ids)
    ]

    if not liked_positions:
        return pd.DataFrame()

    liked_ids = set(liked_google_ids)
    scores = {}

    # Score each candidate against every liked book.
    for candidate_idx in range(len(processed_books)):
        candidate = processed_books.iloc[candidate_idx]
        candidate_id = str(candidate["google_id"])

        # Never recommend a book the user already liked.
        if candidate_id in liked_ids:
            continue

        similarities = [
            float(final_similarity[liked_idx, candidate_idx])
            for liked_idx in liked_positions
        ]

        # Best match to any of the user's liked books.
        score = max(similarities)

        # Small optional bonus for award-winning books.
        is_award_winner = candidate.get("is_award_winner", False)
        if str(is_award_winner).strip().lower() in ("true", "1"):
            score += AWARD_BONUS

        scores[candidate_idx] = score

    ranked_positions = sorted(
        scores,
        key=scores.get,
        reverse=True
    )[:n]

    results = processed_books.iloc[ranked_positions].copy()
    results["final_score"] = [
        scores[i] for i in ranked_positions
    ]
    results["similarity"] = results["final_score"]

    return results

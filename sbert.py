from sentence_transformers import SentenceTransformer
import ast  #turn the author_set back into a set 
import pandas as pd

# Load processed dataset
processed_books = pd.read_csv(r"C:\Users\LOQ\project_books\.venv\datas\processed_books_dataset.csv")

# Load SBERT model ONCE
model = SentenceTransformer("all-MiniLM-L6-v2")

processed_books["author_set"] = processed_books["author_set"].apply(
    ast.literal_eval
)

title_embeddings = model.encode(
    processed_books["title_clean"].fillna("").tolist(),
    show_progress_bar=True
)

category_embeddings = model.encode(
    processed_books["category_clean"].fillna("").tolist(),
    show_progress_bar=True
)

description_embeddings = model.encode(
    processed_books["clean_description"].fillna("").tolist(),
    show_progress_bar=True
)

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

        final_score = similarity + author_bonus

        recommendations.append({
            "index": book_idx,
            "similarity": similarity,
            "author_bonus": author_bonus,
            "final_score": final_score,
            "same_book": same_book
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
        ["title", "authors", "categories"]
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

    return results
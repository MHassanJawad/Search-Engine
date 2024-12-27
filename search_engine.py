from fuzzywuzzy import process
import json
import re
from collections import defaultdict
from nltk.stem import WordNetLemmatizer
import math

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Files and range configurations
barrel_files = [
    "datasets/barrel_1.json",
    "datasets/barrel_2.json",
    "datasets/barrel_3.json",
    "datasets/barrel_4.json",
    "datasets/barrel_5.json"
]

barrel_ranges = [("a", "c"), ("d", "g"), ("h", "i"), ("j", "q"), ("r", "z")]

# Load metadata
with open("datasets/doc_metadata.json", "r") as f:
    doc_metadata = json.load(f)

# Tokenization function
def tokenise(text):
    text = re.sub(r'[^\w\s]', '', text)
    words = str(text).lower().split()

    return [lemmatizer.lemmatize(word) for word in words]

# Load relevant barrels based on tokens
def load_relevant_barrels(query_tokens):
    relevant_barrels = []
    for token in query_tokens:
        first_letter = token[0]
        for i, (start, end) in enumerate(barrel_ranges):
            if start <= first_letter <= end:
                with open(barrel_files[i], "r") as f:
                    relevant_barrels.append(json.load(f))
                break
    return relevant_barrels

# BM25 Calculation Function
def calculate_bm25_score(term, doc_id, inverted_index, avg_doc_len, doc_lengths, total_docs, k1=1.5, b=0.75):
    doc_freq = len(inverted_index.get(term, {}))
    term_freq = inverted_index.get(term, {}).get(doc_id, 0)
    doc_len = doc_lengths.get(doc_id, avg_doc_len)

    if doc_freq == 0 or total_docs == 0:
        return 0

    idf = math.log((total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    numerator = term_freq * (k1 + 1)
    denominator = term_freq + k1 * (1 - b + b * (doc_len / avg_doc_len))
    return idf * (numerator / denominator)

# Fuzzy Search Function to suggest alternatives
def fuzzy_search(query, doc_titles):
    # Extract the closest matches for the query from the document titles
    closest_match = process.extractOne(query, doc_titles)
    if closest_match:
        return closest_match[0]  # Return the closest match
    return None
from fuzzywuzzy import process

# Modify search_query to include fuzzy matching
def search_query(query):
    tokens = tokenise(query)
    relevant_barrels = load_relevant_barrels(tokens)
    if not relevant_barrels:
        return []

    # Load document lengths and total document count
    with open("datasets/doc_lengths.json", "r") as f:
        doc_lengths = json.load(f)
    total_docs = len(doc_lengths)
    avg_doc_len = sum(doc_lengths.values()) / total_docs if total_docs > 0 else 0

    results_bm25 = defaultdict(float)  # BM25 scores
    results_freq = defaultdict(int)   # Frequency scores

    # Fuzzy matching setup for tokens
    all_terms_in_index = set()  # Set to hold all indexed terms (could be fetched from barrel or other indices)
    
    # Populate all_terms_in_index with terms from relevant barrels (e.g., by iterating over the barrel data)
    for barrel in relevant_barrels:
        all_terms_in_index.update(barrel.keys())

    # Now, for each token, use fuzzy matching to suggest the closest term from the indexed terms
    for token in tokens:
        # Use fuzzywuzzy to find the best match from the indexed terms
        closest_match, score = process.extractOne(token, all_terms_in_index)

        # If the score is above a certain threshold (e.g., 80% match), treat it as a valid match
        if score >= 80:  # You can adjust the threshold value
            token = closest_match

        for barrel in relevant_barrels:
            if token not in barrel:
                continue
            for doc_id, freq in barrel[token].items():
                # BM25 Score Calculation
                bm25_score = calculate_bm25_score(
                    token, doc_id, barrel, avg_doc_len, doc_lengths, total_docs
                )
                if bm25_score > 0:
                    results_bm25[doc_id] += bm25_score

                # Frequency-based Score (higher score for title matches)
                results_freq[doc_id] += freq
                title = doc_metadata.get(str(doc_id), {}).get("title", "").lower()
                if token in title:
                    results_freq[doc_id] += freq  # Boost frequency score for title matches

    # Combine results (BM25 prioritized, frequency as a fallback)
    combined_results = defaultdict(float)
    for doc_id in results_bm25:
        # Combine BM25 score and frequency-based score (you can adjust the weighting here)
        combined_results[doc_id] = results_bm25[doc_id] + results_freq.get(doc_id, 0)

    # Sort documents by combined score
    sorted_docs = sorted(combined_results.items(), key=lambda x: x[1], reverse=True)

    search_results = []
    for doc_id, _ in sorted_docs:
        # Get metadata fields: title, description, url, url_to_image
        doc_info = doc_metadata.get(str(doc_id), {})
        title = doc_info.get("title", "No Title Available")
        description = doc_info.get("description", "No Description Available")
        url = doc_info.get("url", "No URL Available")
        url_to_image = doc_info.get("url_to_image", "No Image Available")

        # Add to results
        search_results.append({
            "doc_id": doc_id,
            "title": title,
            "description": description,
            "bm25_score": results_bm25.get(doc_id, 0),
            "frequency_count": results_freq.get(doc_id, 0),
            "score": combined_results[doc_id],
            "url": url,
            "url_to_image": url_to_image
        })

        # Print the document info
        print(f"Doc ID: {doc_id}")
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"URL: {url}")
        print(f"URL to Image: {url_to_image}")
    
    return search_results

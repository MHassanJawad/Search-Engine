from fuzzywuzzy import process
import json
import re
from collections import defaultdict
from nltk.stem import WordNetLemmatizer
import math
import concurrent.futures

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

# Load all barrels into memory at once (only once)
def load_all_barrels():
    barrels = []
    for barrel_file in barrel_files:
        with open(barrel_file, "r") as f:
            barrels.append(json.load(f))
    return barrels

# Load relevant barrels based on tokens (use in-memory barrels)
def load_relevant_barrels(query_tokens, barrels):
    relevant_barrels = []
    for token in query_tokens:
        first_letter = token[0]
        for i, (start, end) in enumerate(barrel_ranges):
            if start <= first_letter <= end:
                relevant_barrels.append(barrels[i])
                break
    return relevant_barrels

# Correct typos using fuzzy matching (with an improved filter)
def correct_typos(tokens, vocabulary, threshold=80):
    corrected_tokens = []
    for token in tokens:
        # Only correct if the token is not already in the vocabulary
        if token not in vocabulary:
            match, score = process.extractOne(token, vocabulary)
            if score >= threshold:
                corrected_tokens.append(match)
            else:
                corrected_tokens.append(token)
        else:
            corrected_tokens.append(token)
    return corrected_tokens

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

# Search query function with optimizations
def search_query(query):
    tokens = tokenise(query)

    # Load all barrels once
    barrels = load_all_barrels()
    
    # Extract vocabulary from all barrels and load relevant barrels
    vocabulary = set()
    for barrel in barrels:
        for token in barrel.keys():
            vocabulary.add(token)

    # Load relevant barrels for the original query
    relevant_barrels = load_relevant_barrels(tokens, barrels)
    
    if not relevant_barrels:
        # If no results found, correct typos and try searching again
        corrected_tokens = correct_typos(tokens, vocabulary)
        relevant_barrels = load_relevant_barrels(corrected_tokens, barrels)
    
    if not relevant_barrels:
        # If still no results, return empty
        return []

    # Load document lengths and total document count
    with open("datasets/doc_lengths.json", "r") as f:
        doc_lengths = json.load(f)
    total_docs = len(doc_lengths)
    avg_doc_len = sum(doc_lengths.values()) / total_docs if total_docs > 0 else 0

    results_bm25 = defaultdict(float)  # BM25 scores
    results_freq = defaultdict(int)   # Frequency scores

    # Function to process a token and update results (to be run in parallel)
    def process_token(token):
        local_results_bm25 = defaultdict(float)
        local_results_freq = defaultdict(int)

        for barrel in relevant_barrels:
            if token not in barrel:
                continue
            for doc_id, freq in barrel[token].items():
                # BM25 Score Calculation
                bm25_score = calculate_bm25_score(
                    token, doc_id, barrel, avg_doc_len, doc_lengths, total_docs
                )
                if bm25_score > 0:
                    local_results_bm25[doc_id] += bm25_score

                # Frequency-based Score (higher score for title matches)
                local_results_freq[doc_id] += freq
                title = doc_metadata.get(str(doc_id), {}).get("title", "").lower()
                if token in title:
                    local_results_freq[doc_id] += freq  # Boost frequency score for title matches

        return local_results_bm25, local_results_freq

    # Parallelize token processing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_token, token) for token in tokens if relevant_barrels]
        for future in concurrent.futures.as_completed(futures):
            local_results_bm25, local_results_freq = future.result()
            for doc_id, score in local_results_bm25.items():
                results_bm25[doc_id] += score
            for doc_id, score in local_results_freq.items():
                results_freq[doc_id] += score

    # Combine results (BM25 prioritized, frequency as a fallback)
    combined_results = defaultdict(float)
    for doc_id in results_bm25:
        combined_results[doc_id] = results_bm25[doc_id] + results_freq.get(doc_id, 0)

    # Sort documents by combined score
    sorted_docs = sorted(combined_results.items(), key=lambda x: x[1], reverse=True)
    return [
        {
            "doc_id": doc_id,
            "title": doc_metadata.get(str(doc_id), {}).get("title", "No Title Available"),
            "description": doc_metadata.get(str(doc_id), {}).get("description", "No Description Available"),
            "url": doc_metadata.get(str(doc_id), {}).get("url", "No URL Available"),
            "url_to_image": doc_metadata.get(str(doc_id), {}).get("url_to_image", "No Image Available"),
            "score": score,
        }
        for doc_id, score in sorted_docs
    ]

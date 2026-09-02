import json
import re
from collections import defaultdict
from nltk.stem import WordNetLemmatizer
import math
from textblob import Word  # Importing Word from TextBlob for spell correction

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Barrel mapping for each letter
barrel_files = {chr(i): f"datasets/barrel_{chr(i)}.json" for i in range(ord('a'), ord('z') + 1)}

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
        if first_letter in barrel_files:
            with open(barrel_files[first_letter], "r") as f:
                relevant_barrels.append(json.load(f))
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

def correct_query_with_textblob(token):
    try:
        return Word(token).spellcheck()[0][0]  # Get the most likely corrected word
    except Exception as e:
        print(f"Error correcting token '{token}': {e}")
        return token  # Return the original token if correction fails


def search_query(query):
    def perform_search(tokens):
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

        # Process tokens
        for token in tokens:
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
            combined_results[doc_id] = results_bm25[doc_id] + results_freq.get(doc_id, 0)

        # Sort documents by combined score
        sorted_docs = sorted(combined_results.items(), key=lambda x: x[1], reverse=True)

        search_results = []
        for doc_id, _ in sorted_docs:
            doc_info = doc_metadata.get(str(doc_id), {})
            title = doc_info.get("title", "No Title Available")
            description = doc_info.get("description", "No Description Available")
            url = doc_info.get("url", "No URL Available")
            url_to_image = doc_info.get("url_to_image", "No Image Available")

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

        return search_results

    # Tokenize the query
    tokens = tokenise(query)

    # Perform the initial search with the original tokens
    results = perform_search(tokens)

    # If no results found, try correcting each token and perform the search again
    if not results:
        corrected_tokens = [correct_query_with_textblob(token) for token in tokens]
        print(f"Original tokens: {tokens}")
        print(f"Corrected tokens: {corrected_tokens}")
        results = perform_search(corrected_tokens)

    # Return total results count and results list
    return {"total_results": len(results), "results": results}
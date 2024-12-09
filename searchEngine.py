import json
import re
from collections import defaultdict
from nltk.stem import WordNetLemmatizer
import nltk

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# File paths for saving indices
forward_index_file = "datasets/forward_index.json"
inverted_index_file = "datasets/inverted_index.json"
lexicon_file = "datasets/lexicon.json"

# Tokenization function with lemmatization
def tokenise(text):
    """Tokenize text into lowercase lemmatized words after removing punctuation."""
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    words = text.lower().split()
    return [lemmatizer.lemmatize(word) for word in words]  # Lemmatize words

# Load indices from JSON files
def load_indices():
    try:
        with open(forward_index_file, "r") as f:
            forward_index = json.load(f)
        with open(inverted_index_file, "r") as f:
            inverted_index = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: Index files not found or invalid. Please generate indices first.")
        return None, None
    return forward_index, inverted_index

def generate_dummy_indices():
    """Generate dummy indices for demonstration purposes."""
    print("Generating dummy indices...")
    documents = {
        "doc1": "The quick brown fox jumps over the lazy dog",
        "doc2": "Python is a programming language",
        "doc3": "Search engines use inverted indices"
    }
    forward_index = {doc_id: tokenise(content) for doc_id, content in documents.items()}
    inverted_index = defaultdict(list)
    for doc_id, tokens in forward_index.items():
        for token in tokens:
            inverted_index[token].append(doc_id)
    return forward_index, dict(inverted_index)

# Search Query
def search_query(query, inverted_index):
    words = tokenise(query)  # Tokenize and lemmatize the query
    results = [set(inverted_index.get(word, [])) for word in words]  # Find the documents for each word

    if results:
        final_results = set.intersection(*results)  # Documents containing all words
    else:
        final_results = set()  # No results if no words in query

    return list(final_results)

# Main function to test the search engine
if __name__ == "__main__":
    forward_index, inverted_index = load_indices()
    if forward_index is None or inverted_index is None:
        exit("Exiting program due to missing or invalid indices.")

    print("Loaded indices from files.")
    # Get user query
    query = input("Enter your search query: ")

    # Search the index
    results = search_query(query, inverted_index)

    if results:
        print(f"Results found in {len(results)} documents: {results}")
    else:
        print("No results found.") 

import json
import re
import pandas as pd
from collections import defaultdict
from nltk.stem import WordNetLemmatizer

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Load the dataset
data_path = "datasets/data.csv"
data = pd.read_csv(data_path)

# File paths
forward_index_file = "datasets/forward_index.json"
lexicon_file = "datasets/lexicon.json"

barrel_files = {chr(i): f"datasets/barrel_{chr(i)}.json" for i in range(ord('a'), ord('z') + 1)}

metadata_file = "datasets/doc_metadata.json"
doc_lengths_file = "datasets/doc_lengths.json"

# Function to ensure all data is stored as strings
def convert_to_string(data):
    """
    Recursively convert all keys and values in a dictionary to strings.
    """
    if isinstance(data, dict):
        return {str(key): convert_to_string(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_string(item) for item in data]
    else:
        return str(data)

# Tokenization function
def tokenise(text):
    text = re.sub(r'[^\w\s]', '', text)
    words = text.lower().split()
    return [lemmatizer.lemmatize(word) for word in words]

# Build indices
def build_indices(articles):
    inverted_index = defaultdict(lambda: defaultdict(int))  # Token -> {DocID -> Frequency}
    forward_index = defaultdict(list)
    doc_metadata = {}
    doc_lengths = {}  # Document lengths for BM25

    for _, row in articles.iterrows():
        doc_id = str(row['article_id'])  # Ensuring that doc_id is a string
        title = str(row.get('title', ''))
        description = str(row.get('description', ''))
        content = ' '.join(row.dropna().astype(str))
        url = str(row.get('url', ''))
        url_to_image = str(row.get('url_to_image', ''))

        # Save metadata
        doc_metadata[doc_id] = {
            "title": title,
            "description": description,
            "url": url,
            "url_to_image": url_to_image,
        }

        # Tokenize content and build indices
        tokens = tokenise(content)
        doc_lengths[doc_id] = len(tokens)  # Store the length of the document
        forward_index[doc_id] = list(map(str, set(tokens)))
        for token in tokens:
            inverted_index[str(token)][doc_id] += 1

    # Divide inverted index into barrels
    barrels = {chr(i): defaultdict(lambda: defaultdict(int)) for i in range(ord('a'), ord('z') + 1)}
    for word, docs in inverted_index.items():
        first_letter = word[0]
        if first_letter in barrels:
            barrels[first_letter][word] = {str(k): int(v) for k, v in docs.items()}

    return (
        convert_to_string(forward_index),
        convert_to_string(barrels),
        convert_to_string(doc_metadata),
        convert_to_string(doc_lengths),
    )

# Save indices to JSON files
def save_indices(forward_index, barrels, doc_metadata, doc_lengths):
    with open(forward_index_file, "w") as f:
        json.dump(forward_index, f, indent=4)

    for letter, barrel in barrels.items():
        with open(barrel_files[letter], "w") as f:
            json.dump(barrel, f, indent=4)

    # Save metadata
    with open(metadata_file, "w") as f:
        json.dump(doc_metadata, f, indent=4)

    # Save document lengths
    with open(doc_lengths_file, "w") as f:
        json.dump(doc_lengths, f, indent=4)

if __name__ == "__main__":
    print("Building indices...")
    forward_index, barrels, doc_metadata, doc_lengths = build_indices(data)
    save_indices(forward_index, barrels, doc_metadata, doc_lengths)
    print("Indices and document lengths saved to JSON files.")

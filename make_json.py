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


lexicon = {}

def tokenise(text):
    text = re.sub(r'[^\w\s]', '', text)
    words = text.lower().split()
    return [lemmatizer.lemmatize(word) for word in words]


def build_indices(articles):
    inverted_index = defaultdict(lambda: defaultdict(int))  # Token -> {DocID -> Frequency}
    forward_index = defaultdict(list)
    doc_metadata = {}
    doc_lengths = {}  # Document lengths for BM25

    for _, row in articles.iterrows():
        doc_id = str(row['article_id'])  # Ensure doc_id is a string
        title = row.get('title', '')
        description = row.get('description', '')
        content = ' '.join(row.dropna().astype(str))
        url = row.get('url')
        url_to_image = row.get('url_to_image')

        # Save metadata
        doc_metadata[doc_id] = {"title": title, "description": description, "url": url, "url_to_image": url_to_image}

        # Tokenize content and build indices
        tokens = tokenise(content)
        doc_lengths[doc_id] = len(tokens)  # Store the length of the document
        forward_index[doc_id] = list(set(tokens))
        for token in tokens:
            inverted_index[token][doc_id] += 1

    # Divide inverted index into barrels
    barrels = {chr(i): defaultdict(lambda: defaultdict(int)) for i in range(ord('a'), ord('z') + 1)}
    for word, docs in inverted_index.items():
        first_letter = word[0]
        if first_letter in barrels:
            barrels[first_letter][word] = docs

    return forward_index, barrels, doc_metadata, doc_lengths

def save_indices(forward_index, barrels, doc_metadata, doc_lengths):
    with open(forward_index_file, "w") as f:
        json.dump(forward_index, f)

    for letter, barrel in barrels.items():
        with open(barrel_files[letter], "w") as f:
            json.dump(barrel, f)

    # Save metadata
    with open(metadata_file, "w") as f:
        json.dump(doc_metadata, f)

    # Save document lengths
    with open(doc_lengths_file, "w") as f:
        json.dump(doc_lengths, f)

if __name__ == "__main__":
    print("Building indices...")
    forward_index, barrels, doc_metadata, doc_lengths = build_indices(data)
    save_indices(forward_index, barrels, doc_metadata, doc_lengths)
    print("Indices and document lengths saved to JSON files.")
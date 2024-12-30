import json
import re
import pandas as pd
from collections import defaultdict
from nltk.stem import WordNetLemmatizer
import os

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


def add_article(article):
    print(article)
    # Helper function to load JSON data
    def load_json(file_path):
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return {}

    # Helper function to save JSON data
    def save_json(data, file_path):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    # Tokenize the content
    doc_id = str(article['article_id'])  # Convert to string for consistency
    title = article.get('title', '')
    description = article.get('description', '')
    content = ' '.join(str(value) for value in article.values() if pd.notna(value))
    url = article.get('url')
    url_to_image = article.get('url_to_image')

    tokens = tokenise(content)

    # Update forward index
    forward_index = load_json(forward_index_file)
    forward_index[doc_id] = list(set(tokens))
    save_json(forward_index, forward_index_file)

    # Update barrels
    for token in tokens:
        first_letter = token[0]
        if first_letter in barrel_files:
            barrel = load_json(barrel_files[first_letter])
            if token not in barrel:
                barrel[token] = {}
            barrel[token][doc_id] = barrel[token].get(doc_id, 0) + 1
            save_json(barrel, barrel_files[first_letter])

    # Update metadata
    doc_metadata = load_json(metadata_file)
    doc_metadata[doc_id] = {
        "title": title,
        "description": description,
        "url": url,
        "url_to_image": url_to_image
    }
    save_json(doc_metadata, metadata_file)

    # Update document lengths
    doc_lengths = load_json(doc_lengths_file)
    doc_lengths[doc_id] = len(tokens)
    save_json(doc_lengths, doc_lengths_file)

    print(f"Article {doc_id} added successfully.")


if __name__ == "__main__":
    # print("Building indices...")
    # forward_index, barrels, doc_metadata, doc_lengths = build_indices(data)
    # save_indices(forward_index, barrels, doc_metadata, doc_lengths)
    # print("Indices and document lengths saved to JSON files.")

    # Example usage of add_article
    new_article = {
        "article_id": 99999,
        "title": "New Dynamic Article",
        "description": "This is a dynamically added article.",
        "url": "http://example.com/new-article",
        "url_to_image": "http://example.com/image.jpg"
    }
    print("Adding a new article...")
    add_article(new_article)

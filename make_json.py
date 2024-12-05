import json
import re
import pandas as pd
from collections import defaultdict

# Load the dataset
data_path = "datasets/data.csv"
data = pd.read_csv(data_path)

# File paths for saving indices
forward_index_file = "datasets/forward_index.json"
inverted_index_file = "datasets/inverted_index.json"
lexicon_file = "datasets/lexicon.json"

# Class to store relevant info about a word in a lexicon
class Word:
    def __init__(self, word_id):
        self.word_id = word_id  # Unique ID for the word
        self.frequency = 0  # Frequency of the word across all documents
        self.doc_freq = 0  # Number of documents containing this word
        self.documents = {}  # Dictionary to store document IDs and word frequencies in each document
    
    def add_document(self, doc_id, count):
        if doc_id not in self.documents:
            self.documents[doc_id] = count
            self.doc_freq += 1  # Increment document frequency for a new document
        else:
            self.documents[doc_id] += count
        self.frequency += count  # Increment total word frequency

    def to_dict(self):
        return {
            "word_id": self.word_id,
            "frequency": self.frequency,
            "doc_freq": self.doc_freq,
            "documents": self.documents
        }

# Initialize an empty dictionary for a lexicon
lexicon = {}

def add_word_to_lexicon(word, doc_id, count):
    if word not in lexicon:
        word_id = hash(word)  # Generate a unique ID for each word
        lexicon[word] = Word(word_id)
    lexicon[word].add_document(doc_id, count)

def lexicon_to_dict():
    return {word: word_obj.to_dict() for word, word_obj in lexicon.items()}

# Tokenization function
def tokenise(text, doc_id):
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    words = text.lower().split()  # Tokenize and convert to lowercase

    word_frequency = defaultdict(int)
    for word in words:
        word_frequency[word] += 1

    # Update the lexicon with word frequency and document ID
    for word, count in word_frequency.items():
        add_word_to_lexicon(word, doc_id, count)
    
    return words

# Build Inverted Index
def build_inverted_index(articles):
    inverted_index = defaultdict(list)

    for _, row in articles.iterrows():
        doc_id = row['article_id']  # Get the article ID
        content = ' '.join(row[['source_name', 'author', 'title', 'description', 
                                'content', 'category', 'full_content']].dropna())  # Combine content
        tokens = tokenise(content, doc_id)  # Tokenize the content and update lexicon
        for token in set(tokens):  # Avoid duplicates for each document
            inverted_index[token].append(doc_id)

    return inverted_index

# Build Forward Index
def build_forward_index(articles):
    forward_index = defaultdict(list)

    for _, row in articles.iterrows():
        doc_id = row['article_id']
        content = ' '.join(row[['source_name', 'author', 'title', 'description', 
                                'content', 'category', 'full_content']].dropna())
        tokens = tokenise(content, doc_id)
        forward_index[doc_id] = list(set(tokens))  # Store unique tokens for each document

    return forward_index

# Save indices to JSON files
def save_indices(forward_index, inverted_index, lexicon):
    with open(forward_index_file, "w") as f:
        json.dump(forward_index, f)
    with open(inverted_index_file, "w") as f:
        json.dump(inverted_index, f)
    with open(lexicon_file, "w") as f:
        json.dump(lexicon_to_dict(), f)

# Main function to generate and save the indices
if __name__ == "__main__":
    print("Building indices...")
    forward_index = build_forward_index(data)
    inverted_index = build_inverted_index(data)
    save_indices(forward_index, inverted_index, lexicon)
    print("Indices saved to JSON files.")

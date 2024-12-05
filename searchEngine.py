import json
import re
from collections import defaultdict

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
        word_id = hash((word, doc_id))  # Use a tuple to ensure unique hashing
        lexicon[word] = Word(word_id)
    lexicon[word].add_document(doc_id, count)

def lexicon_to_dict():
    return {word: word_obj.to_dict() for word, word_obj in lexicon.items()}

def load_lexicon(lexicon_dict):
    global lexicon
    lexicon = {}
    for word, word_data in lexicon_dict.items():
        word_obj = Word(word_data["word_id"])
        word_obj.frequency = word_data["frequency"]
        word_obj.doc_freq = word_data["doc_freq"]
        word_obj.documents = word_data["documents"]
        lexicon[word] = word_obj

# Tokenization function
def tokenise(text):
    """Tokenize text into lowercase words after removing punctuation."""
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text.lower().split()

def update_lexicon_with_tokens(tokens, doc_id):
    """Update lexicon with token frequencies for a specific document."""
    word_frequency = defaultdict(int)
    for word in tokens:
        word_frequency[word] += 1

    for word, count in word_frequency.items():
        add_word_to_lexicon(word, doc_id, count)

# Load indices from JSON files
def load_indices():
    try:
        with open(forward_index_file, "r") as f:
            forward_index = json.load(f)
        with open(inverted_index_file, "r") as f:
            inverted_index = json.load(f)
        with open(lexicon_file, "r") as f:
            load_lexicon(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: Index files not found or invalid. Please generate indices first.")
        return None, None
    return forward_index, inverted_index

# Search Query
def search_query(query, inverted_index):
    words = tokenise(query)  # Tokenize the query
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

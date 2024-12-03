import re
import pandas as pd
from collections import defaultdict

# Load the dataset
data_path = "datasets/data.csv"
rating_path = "datasets/rating.csv"
rawData_path = "datasets/raw-data.csv"

data = pd.read_csv(data_path)
rating = pd.read_csv(rating_path)
rawData = pd.read_csv(rawData_path)

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

    def get_doc_frequency(self):
        return self.doc_freq

    def get_word_frequency(self):
        return self.frequency

    def get_documents(self):
        return self.documents

# Initialize an empty dictionary for a lexicon
lexicon = {}

def add_word_to_lexicon(word, doc_id, count):
    if word not in lexicon:
        word_id = hash(word) + hash(doc_id)  # Generate a unique ID for each word
        lexicon[word] = Word(word_id)
    lexicon[word].add_document(doc_id, count)

def get_word_info(word):
    if word in lexicon:
        word_obj = lexicon[word]
        return {
            "word_id": word_obj.word_id,
            "frequency": word_obj.get_word_frequency(),
            "doc_freq": word_obj.get_doc_frequency(),
            "documents": word_obj.get_documents()
        }
    return None

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
        content = ' '.join(row[['source_name', 'author', 'title', 'description', 'content', 'category', 'full_content']].dropna())  # Combine content
        tokens = tokenise(content, doc_id)  # Tokenize the content and update lexicon
        for token in set(tokens):  # Avoid duplicates for each document
            inverted_index[token].append(doc_id)

    return inverted_index

# Build Forward Index
def build_forward_index(articles):
    forward_index = defaultdict(list)

    for _, row in articles.iterrows():
        doc_id = row['article_id']
        content = ' '.join(row[['source_name', 'author', 'title', 'description', 'content', 'category', 'full_content']].dropna())
        tokens = tokenise(content, doc_id)
        forward_index[doc_id] = list(set(tokens))  # Store unique tokens for each document

    return forward_index

# Search Query
def search_query(query, inverted_index):
    words = tokenise(query, None)  # Tokenize the query
    results = [set(inverted_index.get(word, [])) for word in words]  # Find the documents for each word

    if results:
        final_results = set.intersection(*results)  # Documents containing all words
    else:
        final_results = set()  # No results if no words in query

    return list(final_results)

# Main function to test the search engine
if __name__ == "__main__":
    inverted_index = build_inverted_index(data)

    # Get user query
    query = input("Enter your search query: ")

    # Search the index
    results = search_query(query, inverted_index)

    if results:
        print(f"Results found in {len(results)} documents: {results}")
    else:
        print("No results found.")

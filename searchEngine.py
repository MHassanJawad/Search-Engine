import re
from collections import defaultdict

# A small dataset of documents
documents = {
    "doc1": "Cats are cute animals.",
    "doc2": "Dogs and cats are both common pets.",
    "doc3": "Some people prefer dogs over cats."
}

# Function to preprocess text
def preprocess_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    tokens = text.split()  # Split into words
    return tokens



# Function to build the inverted index
def build_inverted_index(documents):
    inverted_index = defaultdict(list)  # A dictionary with default empty lists
    for doc_id, content in documents.items():
        tokens = preprocess_text(content)
        for token in set(tokens):  # Avoid duplicates for each document
            inverted_index[token].append(doc_id)  # Map the word to the document ID
    return inverted_index

def search_query(query, inverted_index):
    # Preprocess the query (split into words and clean them)
    words = preprocess_text(query)  # Break query into words

    # Find the documents for each word
    results = []
    for word in words:
        results.append(set(inverted_index.get(word, [])))  # Use sets for intersection later

    # Combine results: Find documents containing ALL words
    if results:
        final_results = set.intersection(*results)  # Documents containing all words
    else:
        final_results = set()  # No results if no words in query

    return list(final_results)  # Convert to list for consistency



# Main function to test the search engine
if __name__ == "__main__":
    # Step 1: Build the inverted index
    inverted_index = build_inverted_index(documents)

    # Step 2: Get user query
    query = input("Enter your search query: ")

    # Step 3: Search the index
    results = search_query(query, inverted_index)

    # Step 4: Display the results
    if results:
        print("Results found in documents:", results)
    else:
        print("No results found.")



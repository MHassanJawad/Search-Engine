import json
import re
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn

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
    words = text.lower().split()
    return [lemmatizer.lemmatize(word) for word in words]

# Load relevant barrels based on tokens
def load_relevant_barrels(query_tokens):
    relevant_barrels = []
    for token in query_tokens:
        first_letter = token[0]
        for i, (start, end) in enumerate(barrel_ranges):
            if start <= first_letter <= end:
                with open(barrel_files[i], "r") as f:
                    relevant_barrels.append(json.load(f))
                break
    return relevant_barrels

# Get synonyms of a word using WordNet
def get_synonyms(word):
    synonyms = set()
    for syn in wn.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower())  # Add the synonym in lowercase
    return synonyms

# Expand query tokens to include lemmas and synonyms
def expand_query_tokens(tokens):
    expanded_terms = set()
    for token in tokens:
        expanded_terms.add(token)  # Add original token
        expanded_terms.add(lemmatizer.lemmatize(token))  # Add lemma
        expanded_terms.update(get_synonyms(token))  # Add synonyms
    return expanded_terms

# Search query function
def search_query(query):
    tokens = tokenise(query)
    expanded_tokens = expand_query_tokens(tokens)  # Expand tokens

    # Load barrels only once
    relevant_barrels = {}
    for token in expanded_tokens:
        first_letter = token[0]
        for i, (start, end) in enumerate(barrel_ranges):
            if start <= first_letter <= end:
                if i not in relevant_barrels:  # Load each barrel only once
                    with open(barrel_files[i], "r") as f:
                        relevant_barrels[i] = json.load(f)
                break

    results = {}
    # Search for all expanded tokens in the preloaded barrels
    for token in expanded_tokens:
        for barrel in relevant_barrels.values():
            if token in barrel:
                if token not in results:
                    results[token] = set()
                results[token].update(barrel[token])  # Add matching documents

    # Collect matching documents
    if results:
        # Union of all token results
        matching_docs = set.union(*results.values())
        
        # Prepare the results
        result_list = []
        for doc in matching_docs:
            matched_words = [
                token for token, docs in results.items() if doc in docs
            ]
            
            # Append the document details
            result_list.append({
                "doc_id": doc,
                "title": doc_metadata.get(str(doc), {}).get("title", "No Title Available"),
                "description": doc_metadata.get(str(doc), {}).get("description", "No Description Available"),
                "matched_words": matched_words
            })
        
        return result_list  # Return the final list of results
    
    return []

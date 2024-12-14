import json
import re
from nltk.stem import WordNetLemmatizer

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Barrel file paths
barrel_files = ["datasets/barrel_1.json", "datasets/barrel_2.json", 
                "datasets/barrel_3.json", "datasets/barrel_4.json", 
                "datasets/barrel_5.json"]

# Barrel ranges
barrel_ranges = [("a", "c"), ("d", "g"), ("h", "i"), ("j", "q"), ("r", "z")]

def tokenise(text):
    text = re.sub(r'[^\w\s]', '', text)
    words = text.lower().split()
    return [lemmatizer.lemmatize(word) for word in words]

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

def search_query(query):
    tokens = tokenise(query)
    relevant_barrels = load_relevant_barrels(tokens)

    results = []
    for token in tokens:
        docs = set()
        for barrel in relevant_barrels:
            docs.update(barrel.get(token, []))
        results.append(docs)

    if results:
        return list(set.intersection(*results))
    return []

if __name__ == "__main__":
    query = input("Enter your search query: ")
    results = search_query(query)

    if results:
        print(f"Results found in {len(results)} documents: {results}")
    else:
        print("No results found.")

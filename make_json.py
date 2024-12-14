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
barrel_files = ["datasets/barrel_1.json", "datasets/barrel_2.json", 
                "datasets/barrel_3.json", "datasets/barrel_4.json", 
                "datasets/barrel_5.json"]

# Define barrels based on first letter
barrel_ranges = [
    ("a", "e"), ("f", "j"), ("k", "o"), ("p", "t"), ("u", "z")
]

# Class for word metadata in lexicon
class Word:
    def __init__(self, word_id):
        self.word_id = word_id
        self.frequency = 0
        self.doc_freq = 0
        self.documents = {}

    def add_document(self, doc_id, count):
        if doc_id not in self.documents:
            self.documents[doc_id] = count
            self.doc_freq += 1
        else:
            self.documents[doc_id] += count
        self.frequency += count

    def to_dict(self):
        return {
            "word_id": self.word_id,
            "frequency": self.frequency,
            "doc_freq": self.doc_freq,
            "documents": self.documents
        }

lexicon = {}

def add_word_to_lexicon(word, doc_id, count):
    if word not in lexicon:
        word_id = hash(word)
        lexicon[word] = Word(word_id)
    lexicon[word].add_document(doc_id, count)

def lexicon_to_dict():
    return {word: word_obj.to_dict() for word, word_obj in lexicon.items()}

def tokenise(text, doc_id):
    text = re.sub(r'[^\w\s]', '', text)
    words = text.lower().split()
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]

    word_frequency = defaultdict(int)
    for word in lemmatized_words:
        word_frequency[word] += 1

    for word, count in word_frequency.items():
        add_word_to_lexicon(word, doc_id, count)

    return lemmatized_words

def build_indices(articles):
    inverted_index = defaultdict(list)
    forward_index = defaultdict(list)

    for _, row in articles.iterrows():
        doc_id = row['article_id']
        content = ' '.join(row.dropna().astype(str))
        tokens = tokenise(content, doc_id)

        forward_index[doc_id] = list(set(tokens))
        for token in set(tokens):
            inverted_index[token].append(doc_id)

    # Divide inverted index into barrels
    barrels = [defaultdict(list) for _ in range(len(barrel_ranges))]
    for word, docs in inverted_index.items():
        first_letter = word[0]
        for i, (start, end) in enumerate(barrel_ranges):
            if start <= first_letter <= end:
                barrels[i][word] = docs
                break

    return forward_index, barrels

def save_indices(forward_index, barrels):
    with open(forward_index_file, "w") as f:
        json.dump(forward_index, f)

    for i, barrel in enumerate(barrels):
        with open(barrel_files[i], "w") as f:
            json.dump(barrel, f)

    with open(lexicon_file, "w") as f:
        json.dump(lexicon_to_dict(), f)

if __name__ == "__main__":
    print("Building indices...")
    forward_index, barrels = build_indices(data)
    save_indices(forward_index, barrels)
    print("Indices saved to JSON files.")

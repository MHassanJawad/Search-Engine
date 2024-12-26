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
metadata_file = "datasets/doc_metadata.json"

# Define barrels based on first letter
barrel_ranges = [("a", "c"), ("d", "g"), ("h", "i"), ("j", "q"), ("r", "z")]

lexicon = {}

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

    def get_doc_frequency(self):
        return self.doc_freq

    def get_word_frequency(self):
        return self.frequency

    def get_documents(self):
        return self.documents


def addToLexicon(word, doc_id, count):
    if word not in lexicon:
        word_id = hash(word) + hash(doc_id)
        lexicon[word] = Word(word_id)
    lexicon[word].add_document(doc_id, count)


def tokenise(text, doc_id):
    text = re.sub(r'[^\w\s]', '', text)
    words = text.lower().split()
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]

    word_frequency = defaultdict(int)
    for word in lemmatized_words:
        word_frequency[word] += 1

    for word, count in word_frequency.items():
        addToLexicon(word, doc_id, count)
    
    return lemmatized_words


def build_indices(articles):
    inverted_index = defaultdict(list)
    forward_index = defaultdict(list)
    doc_metadata = {}

    for _, row in articles.iterrows():
        doc_id = row['article_id']
        title = row.get('title', '')
        description = row.get('description', '')
        content = ' '.join(row.dropna().astype(str))

        doc_metadata[doc_id] = {"title": title, "description": description}

        tokens = tokenise(content, doc_id)
        forward_index[doc_id] = list(set(tokens))
        for token in set(tokens):
            inverted_index[token].append(doc_id)

    barrels = [defaultdict(list) for _ in range(len(barrel_ranges))]
    for word, docs in inverted_index.items():
        first_letter = word[0]
        for i, (start, end) in enumerate(barrel_ranges):
            if start <= first_letter <= end:
                barrels[i][word] = docs
                break

    return forward_index, barrels, doc_metadata


def save_lexicon(lexicon, lexicon_file):
    lexicon_data = {}
    for word, word_obj in lexicon.items():
        lexicon_data[word] = {
            "word_id": word_obj.word_id,
            "frequency": word_obj.get_word_frequency(),
            "doc_freq": word_obj.get_doc_frequency(),
            "documents": word_obj.get_documents()
        }
    
    with open(lexicon_file, "w") as f:
        json.dump(lexicon_data, f, indent=4)


def save_indices(forward_index, barrels, doc_metadata, lexicon):
    with open(forward_index_file, "w") as f:
        json.dump(forward_index, f, indent=4)

    for i, barrel in enumerate(barrels):
        with open(barrel_files[i], "w") as f:
            json.dump(barrel, f, indent=4)

    with open(metadata_file, "w") as f:
        json.dump(doc_metadata, f, indent=4)

    save_lexicon(lexicon, lexicon_file)


if __name__ == "__main__":
    print("Building indices...")
    forward_index, barrels, doc_metadata = build_indices(data)
    save_indices(forward_index, barrels, doc_metadata, lexicon)
    print("Indices and lexicon saved to JSON files.")

import re
import pandas as pd
from collections import defaultdict
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk import word_tokenize, pos_tag

#load the dataset
data_path = "datasets/data.csv"
rating_path = "datasets/rating.csv"
rawData_path = "datasets/raw-data.csv"

data = pd.read_csv(data_path)
rating = pd.read_csv(rating_path)
rawData = pd.read_csv(rawData_path)

#make a class to store relevant info about a word in a lexicon
class Word:
    def __init__(self, word_id):
        self.word_id = word_id  #unique ID for the word
        self.frequency = 0  #frequency of the word across all documents
        self.doc_freq = 0  #number of documents containing this word
        self.documents = {}  #dictionary to store document IDs and word frequencies in each document
    
    def add_document(self, doc_id, count):  #count represents the number of time the word appears in this document
        if doc_id not in self.documents:
            self.documents[doc_id] = count
            self.doc_freq += 1  #increment document frequency if it's a new document
        else:
            self.documents[doc_id] += count  #increment word count if document is already in the dictionary
            self.frequency += count  #increment total word frequency

    def get_doc_frequency(self):
        return self.doc_freq

    def get_word_frequency(self):
        return self.frequency

    def get_documents(self):
        return self.documents


#initialize an empty dictionary for a lexicon
lexicon = {}

def addToLexicon(word, doc_id, count):

    #if the word is not in the lexicon, create a new Word object
    if word not in lexicon:
        word_id = hash(word) + hash(doc_id)  #use hash function to generate a unique ID for each word
        lexicon[word] = Word(word_id)
    
    #add the document and frequency information to the Word object
    lexicon[word].add_document(doc_id, count)

def getWordInfo(word):
    if word in lexicon:
        word_obj = lexicon[word]
        return {
            "word_id": word_obj.word_id,
            "frequency": word_obj.get_word_frequency(),
            "doc_freq": word_obj.get_doc_frequency(),
            "documents": word_obj.get_documents()
        }
    else:
        return None
    

#tokenization function 
def tokenise(text, doc_id):
    text = re.sub(r'[^\w\s]', '', text)  #remove punctuation
    words = text.lower().split()  #tokenize and convert to lowercase

    # count the frequency of each word and update the lexicon
    word_frequency = defaultdict(int)
    for word in words:
        word_frequency[word] += 1

    #update the lexicon with word frequency and document ID
    for word, count in word_frequency.items():
        addToLexicon(word, doc_id, count)
    
    return words  #return the tokenized words 


#build Inverted Index
def build_inverted_index(articles):
    inverted_index = defaultdict(list)  

    for _, row in articles.iterrows(): 
        doc_id = row['article_id']  #get the article ID

        #use values from these columns for tokenisation
        content = ' '.join(row[['source_name', 'author', 'title', 'description', 'content', 'category', 'full_content']].dropna())

        tokens = tokenise(content, doc_id)  #tokenise the content of the article and update lexicon
        for token in set(tokens):  #avoid duplicates for each document
            inverted_index[token].append(doc_id)  #map the token to the document ID

    return inverted_index

#build Forward Index
def forwardIndex(articles):
    forward_index = defaultdict(list)

    for _, row in articles.iterrows():
        doc_id = row['article_id']
        content = ' '.join(row[['source_name', 'author', 'title', 'description', 'content', 'category', 'full_content']].dropna())

        tokens = tokenise(content, doc_id)
        unique_tokens = set(tokens)     #store unique tokens for each document
        forward_index[doc_id] = list(unique_tokens)
    
    return forward_index



def get_wordnet_pos(treebank_tag):
    
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN  

# lemmatization with correct POS
def lemmatize(word):
    token = word_tokenize(word)
    lemmatizer = WordNetLemmatizer()
    pos_tagged = pos_tag(token)  #get POS tags for the tokenized words
    lemma = [
        lemmatizer.lemmatize(word, get_wordnet_pos(tag))
        for word, tag in pos_tagged
    ]
    return " ".join(lemma)



def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.append(lemma.name())
    return set(synonyms)  #return unique synonyms


def search_query(query, inverted_index):
    #tokenise and process the query
    words = tokenise(query, None)

    results = []
    
    lemmatizer = WordNetLemmatizer()
    
    for word in words:
        #search for the original word in the index
        word_results = set(inverted_index.get(word, []))
        results.append(word_results)

        #lemmatize the word and search for its lemma
        lemma = lemmatizer.lemmatize(word)
        lemma_results = set(inverted_index.get(lemma, []))
        results.append(lemma_results)

        #get synonyms of the word and search for each synonym
        synonyms = get_synonyms(word)
        for synonym in synonyms:
            synonym_results = set(inverted_index.get(synonym, []))
            results.append(synonym_results)

    #find documents containing all query terms
    if results:
        final_results = set.intersection(*results) if all(results) else set()
    else:
        final_results = set()

    return list(final_results)


#main function to test the search engine
if __name__ == "__main__":
  
    inverted_index = build_inverted_index(data)

    # get user query
    query = input("Enter your search query: ")

    #search the index
    results = search_query(query, inverted_index)

    #diisplay the results
    if results:
        print("Results found in {len(results)} documents:", {results})
    else:
        print("No results found.")

import re
from collections import defaultdict
from myenv.kaggle import data, rating, rawData


#data to tokenise
#tokenData = data[['sourcename','author','title', 'description', 'content', 'category', 'fullcontent']]


# Function to preprocess text
from collections import defaultdict

# Assuming 'tokenise' is your text preprocessing function
def tokenise(text):
    # Your tokenization logic (e.g., lowercasing, removing punctuation, etc.)
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text.lower().split()



def build_inverted_index(articles):
    inverted_index = defaultdict(list)  # A dictionary with default empty lists

    # Iterate through each article (assuming articles is a pandas DataFrame)
    for _, row in articles.iterrows():  # Iterate over each row in the DataFrame
        doc_id = row['article_id']  # Get the article ID
        content = ' '.join(row[['source_name', 'author', 'title', 'description', 'content', 'category', 'full_content']].dropna())   # Get the content of the article

        tokens = tokenise(content)  # Tokenize the content of the article
        for token in set(tokens):  # Avoid duplicates for each document
            inverted_index[token].append(doc_id)  # Map the token to the document ID

    return inverted_index



def search_query(query, inverted_index):
    # Preprocess the query (split into words and clean them)
    words = tokenise(query)  # Break query into words

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



# main function to test the search engine
if __name__ == "__main__":
    # build the inverted index for the selected columns
    inverted_index = build_inverted_index(data)

    # Get user query
    query = input("Enter your search query: ")

    # Search the index
    results = search_query(query, inverted_index)

    # Display the results
    if results:
        print("Results found in documents:", results)
    else:
        print("No results found.")



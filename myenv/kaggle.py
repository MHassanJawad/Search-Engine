import pandas as pd

# Load the dataset
data_path = "datasets/data.csv"
rating_path = "datasets/rating.csv"
rawData_path = "datasets/raw-data.csv"

data = pd.read_csv(data_path)
rating = pd.read_csv(rating_path)
rawData = pd.read_csv(rawData_path)

# Access the data
print(data.head())  # View the first few rows
print(data.columns)  # See the column names

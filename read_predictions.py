import os
import requests
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DATABRICKS_HOST")
token = os.getenv("DATABRICKS_TOKEN")

file_path = (
    "/Volumes/workspace/supply_chain_db/"
    "supply_chain_data/stockout_predictions.csv"
)

url = f"{host}/api/2.0/fs/files{file_path}"

headers = {
    "Authorization": f"Bearer {token}"
}

print("Connecting to Databricks...")

response = requests.get(
    url,
    headers=headers,
    stream=True
)

response.raise_for_status()

with open("stockout_predictions.csv", "wb") as file:
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            file.write(chunk)

print("Predictions downloaded successfully!")
print("Saved as: stockout_predictions.csv")

import pandas as pd

df = pd.read_csv("stockout_predictions.csv")

print("\nDataset shape:", df.shape)
print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 5 records:")
print(df.head())
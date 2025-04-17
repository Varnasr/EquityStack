"""Read large CSV file in chunks and process each batch."""
import pandas as pd

def read_large_csv(file_path, chunk_size=10000):
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        yield chunk
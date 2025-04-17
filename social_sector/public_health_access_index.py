"""Generate simple binary access index from multiple variables."""
import pandas as pd

def compute_access_index(df, access_columns):
    df['access_index'] = df[access_columns].mean(axis=1)
    return df
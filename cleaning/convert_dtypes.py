"""Convert columns to appropriate dtypes with fallback handling."""
import pandas as pd

def convert_column_types(df, column_types):
    for col, dtype in column_types.items():
        try:
            df[col] = df[col].astype(dtype)
        except Exception as e:
            print(f"Could not convert {col} to {dtype}: {e}")
    return df
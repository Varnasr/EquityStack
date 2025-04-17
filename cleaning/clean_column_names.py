"""Rename DataFrame columns to snake_case format using a reusable function."""
import pandas as pd
import re

def clean_column_names(df):
    df.columns = [re.sub(r'\W+', '_', col).lower().strip('_') for col in df.columns]
    return df
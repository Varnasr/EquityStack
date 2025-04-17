"""Handle missing data by filling, dropping, or flagging nulls."""
import pandas as pd

def handle_missing(df, strategy='drop', fill_value=None):
    if strategy == 'drop':
        return df.dropna()
    elif strategy == 'fill':
        return df.fillna(fill_value)
    elif strategy == 'flag':
        for col in df.columns:
            df[f'{col}_missing'] = df[col].isna().astype(int)
        return df
    else:
        raise ValueError("Invalid strategy")
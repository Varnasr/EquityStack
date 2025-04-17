from cleaning.handle_missing_values import handle_missing
import pandas as pd
import numpy as np

def test_handle_missing_fill():
    df = pd.DataFrame({"a": [1, np.nan, 3]})
    result = handle_missing(df, strategy='fill', fill_value=0)
    assert result.isna().sum().sum() == 0
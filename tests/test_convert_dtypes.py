from cleaning.convert_dtypes import convert_column_types
import pandas as pd

def test_convert_column_types():
    df = pd.DataFrame({"a": ["1", "2", "3"]})
    out = convert_column_types(df, {"a": int})
    assert out["a"].dtype == int
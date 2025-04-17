from cleaning.clean_column_names import clean_column_names
import pandas as pd

def test_clean_column_names():
    df = pd.DataFrame({"First Name": ["Alice"], "Age (Years)": [30]})
    cleaned = clean_column_names(df)
    assert list(cleaned.columns) == ["first_name", "age_years"]
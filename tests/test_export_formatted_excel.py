from io_helpers.export_formatted_excel import export_summary_to_excel
import pandas as pd
import os

def test_export_excel():
    df = pd.DataFrame({"a": [1, 2, 3]})
    export_summary_to_excel(df, "test_output.xlsx")
    assert os.path.exists("test_output.xlsx")
    os.remove("test_output.xlsx")
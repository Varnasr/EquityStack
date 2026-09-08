import pandas as pd

from io_helpers.export_formatted_excel import export_summary_to_excel


def test_export_excel(tmp_path):
    # Previously written into the repository root and removed afterwards, which
    # leaves the file behind whenever the assertion fails.
    out = tmp_path / "test_output.xlsx"
    df = pd.DataFrame({"a": [1, 2, 3]})

    export_summary_to_excel(df, str(out))

    assert out.exists()
    assert out.stat().st_size > 0

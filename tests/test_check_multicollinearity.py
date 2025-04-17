from modelling.check_multicollinearity import calculate_vif
import pandas as pd

def test_vif_output():
    df = pd.DataFrame({"x1": [1, 2, 3, 4, 5], "x2": [2, 4, 6, 8, 10]})
    result = calculate_vif(df, ["x1", "x2"])
    assert "vif" in result.columns
    assert len(result) == 2
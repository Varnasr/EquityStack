from social_sector.public_health_access_index import compute_access_index
import pandas as pd

def test_access_index():
    df = pd.DataFrame({"toilet": [1, 0, 1], "water": [1, 1, 0]})
    result = compute_access_index(df, ["toilet", "water"])
    assert "access_index" in result.columns
    assert result["access_index"].between(0, 1).all()
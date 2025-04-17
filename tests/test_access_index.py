from social_sector.public_health_access_index import compute_access_index
import pandas as pd

def test_access_index_range():
    df = pd.DataFrame({"a": [1, 0, 1], "b": [0, 1, 1]})
    out = compute_access_index(df, ["a", "b"])
    assert out["access_index"].between(0, 1).all()
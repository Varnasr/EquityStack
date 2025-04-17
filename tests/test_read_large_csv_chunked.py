from io_helpers.read_large_csv_chunked import read_large_csv
import pandas as pd

def test_read_chunks():
    with open("sample_data/gender_sample.csv", "w") as f:
        f.write("a,b\n1,2\n3,4\n5,6\n")
    chunks = list(read_large_csv("sample_data/gender_sample.csv", chunk_size=2))
    assert len(chunks) == 2
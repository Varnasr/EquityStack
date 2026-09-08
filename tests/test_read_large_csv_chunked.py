from io_helpers.read_large_csv_chunked import read_large_csv


def test_read_chunks(tmp_path):
    # This test used to write its throwaway rows straight into
    # sample_data/gender_sample.csv, destroying the committed sample data on
    # every run. It survived only because nobody committed the damage. Write to
    # the temporary directory pytest provides instead.
    path = tmp_path / "chunked.csv"
    path.write_text("a,b\n1,2\n3,4\n5,6\n")

    chunks = list(read_large_csv(str(path), chunk_size=2))
    assert len(chunks) == 2
    assert sum(len(c) for c in chunks) == 3


def test_the_sample_data_is_left_alone(tmp_path):
    """A test must not modify files the repository tracks."""
    import hashlib
    import pathlib

    sample = pathlib.Path(__file__).resolve().parent.parent / "sample_data" / "gender_sample.csv"
    before = hashlib.sha256(sample.read_bytes()).hexdigest()

    path = tmp_path / "scratch.csv"
    path.write_text("a,b\n1,2\n")
    list(read_large_csv(str(path), chunk_size=1))

    assert hashlib.sha256(sample.read_bytes()).hexdigest() == before

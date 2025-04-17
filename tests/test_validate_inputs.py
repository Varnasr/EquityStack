from validation.validate_inputs_pydantic import Config
import pytest

def test_valid_config():
    cfg = Config(input_path="data.csv", report_year=2022)
    assert cfg.report_year == 2022

def test_invalid_year():
    with pytest.raises(ValueError):
        Config(input_path="data.csv", report_year=1990)
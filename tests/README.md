# Test Suite for Snippets Repository

This folder contains automated tests for all core `.py` scripts in the repo.  
These are **sanity checks** to ensure that each function runs with expected inputs and does not raise errors.

## 🔧 How to Run

1. Install dependencies:

```
pip install -r requirements.txt
pip install pytest
```

2. Run the test suite:

```
pytest tests/
```

## 🧪 Coverage

This suite tests:

- Data cleaning (`clean_column_names`, `handle_missing_values`, `convert_dtypes`)
- IO helpers (read large CSVs, Excel export)
- Modelling (VIF checks)
- Visualisation (annotated bar charts)
- Validation (with `pydantic`)
- Social sector metrics (access index)

Tests use simulated or temporary in-memory data — no external inputs are required.


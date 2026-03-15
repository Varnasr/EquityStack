"""
Reusable data cleaning pipeline for survey data.
Handles common cleaning tasks: deduplication, missing values, type conversion,
categorical standardisation, and cleaning log generation.
"""

import pandas as pd
import numpy as np
from datetime import datetime


class CleaningPipeline:
    """Pipeline for cleaning survey data with automatic logging."""

    def __init__(self, df, id_col=None):
        self.df = df.copy()
        self.original_shape = df.shape
        self.id_col = id_col
        self.log = []
        self._log_step("Loaded data", f"{df.shape[0]} rows, {df.shape[1]} columns")

    def _log_step(self, step, detail):
        self.log.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "detail": detail,
            "rows": len(self.df),
        })

    def remove_duplicates(self, subset=None):
        """Remove duplicate rows, optionally by subset of columns."""
        before = len(self.df)
        if subset is None:
            subset = [self.id_col] if self.id_col else None
        self.df = self.df.drop_duplicates(subset=subset)
        removed = before - len(self.df)
        self._log_step("Remove duplicates", f"Removed {removed} duplicates")
        return self

    def standardize_columns(self):
        """Lowercase and snake_case all column names."""
        import re
        self.df.columns = [
            re.sub(r"[^a-z0-9]+", "_", col.lower().strip()).strip("_")
            for col in self.df.columns
        ]
        self._log_step("Standardize columns", f"{len(self.df.columns)} columns renamed")
        return self

    def handle_missing(self, strategy="drop", threshold=0.5, fill_value=None):
        """
        Handle missing values.
        strategy: 'drop' drops rows above threshold, 'fill' fills with value,
                  'median' fills numeric with median, 'mode' fills with mode
        """
        before = len(self.df)
        if strategy == "drop":
            # Drop columns with too many missing values
            col_threshold = len(self.df) * threshold
            cols_before = len(self.df.columns)
            self.df = self.df.dropna(axis=1, thresh=int(col_threshold))
            dropped_cols = cols_before - len(self.df.columns)
            self._log_step("Drop sparse columns", f"Dropped {dropped_cols} columns (>{threshold*100}% missing)")
        elif strategy == "fill":
            self.df = self.df.fillna(fill_value)
            self._log_step("Fill missing", f"Filled with {fill_value}")
        elif strategy == "median":
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            self.df[numeric_cols] = self.df[numeric_cols].fillna(self.df[numeric_cols].median())
            self._log_step("Median imputation", f"Filled {len(numeric_cols)} numeric columns")
        elif strategy == "mode":
            for col in self.df.columns:
                if self.df[col].isna().any():
                    self.df[col] = self.df[col].fillna(self.df[col].mode().iloc[0] if len(self.df[col].mode()) > 0 else np.nan)
            self._log_step("Mode imputation", "Filled categorical columns with mode")
        return self

    def convert_types(self, type_map):
        """
        Convert column types.
        type_map: dict of {column_name: target_type} e.g. {"age": "int", "date": "datetime"}
        """
        for col, dtype in type_map.items():
            if col not in self.df.columns:
                continue
            try:
                if dtype == "datetime":
                    self.df[col] = pd.to_datetime(self.df[col], errors="coerce")
                elif dtype == "numeric":
                    self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                else:
                    self.df[col] = self.df[col].astype(dtype)
            except (ValueError, TypeError):
                self._log_step("Type conversion failed", f"{col} -> {dtype}")
        self._log_step("Convert types", f"Converted {len(type_map)} columns")
        return self

    def flag_outliers(self, columns, method="iqr", factor=1.5):
        """Flag outliers using IQR method. Adds _outlier boolean columns."""
        for col in columns:
            if col not in self.df.columns or not np.issubdtype(self.df[col].dtype, np.number):
                continue
            q1 = self.df[col].quantile(0.25)
            q3 = self.df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - factor * iqr
            upper = q3 + factor * iqr
            self.df[f"{col}_outlier"] = (self.df[col] < lower) | (self.df[col] > upper)
            n_outliers = self.df[f"{col}_outlier"].sum()
            self._log_step("Flag outliers", f"{col}: {n_outliers} outliers (IQR x{factor})")
        return self

    def get_result(self):
        """Return cleaned DataFrame."""
        self._log_step("Pipeline complete",
                       f"{self.original_shape[0]} -> {len(self.df)} rows")
        return self.df

    def get_log(self):
        """Return cleaning log as DataFrame."""
        return pd.DataFrame(self.log)

    def save_log(self, path):
        """Save cleaning log to CSV."""
        self.get_log().to_csv(path, index=False)
        self._log_step("Log saved", path)


if __name__ == "__main__":
    # Demo with sample data
    np.random.seed(42)
    raw = pd.DataFrame({
        "Respondent ID": range(1, 101),
        "Age": np.random.randint(18, 65, 100).astype(float),
        "Gender": np.random.choice(["M", "F", "m", "f", None], 100),
        "Income (Rs)": np.random.normal(25000, 8000, 100),
        "Education Years": np.random.choice([None, 5, 8, 10, 12, 14, 16], 100),
        "District": np.random.choice(["Patna", "Ranchi", "patna", "RANCHI"], 100),
    })
    # Add some duplicates
    raw = pd.concat([raw, raw.iloc[:5]], ignore_index=True)

    pipeline = CleaningPipeline(raw, id_col="respondent_id")
    cleaned = (
        pipeline
        .standardize_columns()
        .remove_duplicates()
        .handle_missing(strategy="median")
        .flag_outliers(["age", "income_rs"])
        .get_result()
    )

    print("=== Cleaning Log ===")
    print(pipeline.get_log()[["step", "detail", "rows"]].to_string(index=False))
    print(f"\nCleaned shape: {cleaned.shape}")

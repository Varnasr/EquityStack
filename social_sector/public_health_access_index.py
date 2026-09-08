"""Public health access index: a thin wrapper over the composite machinery.

Kept because two tests and any existing script import `compute_access_index`
from here. It now delegates to `social_sector.composite_index`, which makes the
three decisions an index needs (direction, normalisation, weights) explicit
instead of assuming them.

The original was a bare row mean over the raw columns. That is fine when every
indicator is already a 0-1 coverage share pointing the same way, which is the
case this function still serves, and wrong the moment one of them is a mortality
rate or a rupee figure, which is why the default now normalises.
"""

from __future__ import annotations

import pandas as pd

from .composite_index import composite_index

__all__ = ["compute_access_index"]


def compute_access_index(df, access_columns, *, normalise: bool = False,
                         directions: dict | None = None,
                         weights: dict | None = None,
                         column: str = "access_index") -> pd.DataFrame:
    """Mean access across several indicators, appended as a new column.

    Parameters
    ----------
    normalise
        ``False`` (the default, and the original behaviour) averages the
        columns as they stand. Correct only where every indicator is already on
        the same scale and pointing the same way, which for a set of coverage
        percentages it is.
        ``True`` min-max normalises each indicator first, which is what you
        want the moment the units differ.
    directions
        ``{column: 'lower_is_better'}`` for any indicator where high is bad.
        Requires ``normalise=True``, because flipping a raw unnormalised
        indicator has no defined meaning.

    For anything beyond this, call `composite_index` directly: it offers
    goalpost normalisation for cross-year comparability, geometric aggregation
    where indicators should not substitute for each other, and a minimum
    non-missing count so a district reporting two of six indicators is not
    scored as though it reported all six.

    >>> import pandas as pd
    >>> d = pd.DataFrame({"toilet": [0.8, 0.4], "water": [0.6, 0.2]})
    >>> compute_access_index(d, ["toilet", "water"])["access_index"].tolist()
    [0.7000000000000001, 0.30000000000000004]
    """
    df = pd.DataFrame(df)
    missing = [c for c in access_columns if c not in df.columns]
    if missing:
        raise KeyError(f"compute_access_index: no column(s) {missing} in the frame")

    if directions and not normalise:
        raise ValueError(
            "compute_access_index: directions needs normalise=True. Flipping a raw "
            "indicator that has not been put on a 0-1 scale has no defined meaning.")

    if not normalise:
        out = df.copy()
        out[column] = df[list(access_columns)].mean(axis=1)
        return out

    scored = composite_index(df, list(access_columns), method="minmax",
                             directions=directions, weights=weights, name=column)
    return scored.drop(columns=[c for c in scored.columns if c.endswith("__norm")])

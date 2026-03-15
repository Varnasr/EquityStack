"""
Regression Discontinuity Design for sharp cutoff-based evaluation.
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf


def sharp_rdd(df, outcome, running_var, cutoff=0.0, bandwidth=None):
    """
    Estimate sharp RDD effect using local linear regression.
    Treatment assigned when running_var < cutoff.

    Parameters
    ----------
    bandwidth : float, optional - restrict to observations within bandwidth of cutoff
    """
    df = df.copy()
    if bandwidth is not None:
        df = df[abs(df[running_var] - cutoff) <= bandwidth]

    df["_above"] = (df[running_var] >= cutoff).astype(int)
    df["_centered"] = df[running_var] - cutoff
    model = smf.ols(f"{outcome} ~ _above + _centered + _above:_centered", data=df).fit()
    return model


def optimal_bandwidth_ik(df, running_var, cutoff=0.0):
    """
    Simple bandwidth selection using Imbens-Kalyanaraman (2012) rule of thumb.
    Returns suggested bandwidth.
    """
    centered = df[running_var] - cutoff
    h = 1.06 * centered.std() * len(centered) ** (-0.2)
    return round(h, 2)


def density_test(df, running_var, cutoff=0.0):
    """
    McCrary-style density test. Checks for manipulation of the running variable.
    Large imbalance suggests units may be sorting around the cutoff.
    """
    below = len(df[df[running_var] < cutoff])
    above = len(df[df[running_var] >= cutoff])
    total = below + above
    ratio = below / max(above, 1)
    return {
        "n_below": below,
        "n_above": above,
        "ratio": round(ratio, 2),
        "manipulation_concern": abs(ratio - 1) > 0.3,
    }

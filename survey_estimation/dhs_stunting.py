"""
Worked example: child stunting by wealth quintile from a DHS children's recode,
with design-based standard errors, checked against the figures DHS published.

This is the second half of a two-repo chain. InsightStack's
`data_starters/dhs-south-asia/` turns the raw recode into a clean CSV:

    python load_dhs.py IAKR7EFL.DTA --vars v190 v025 hw70 b5 --anthro \
        --out nfhs5_children.csv

and this script takes it from there:

    python -m survey_estimation.dhs_stunting nfhs5_children.csv

The two are coupled through a file rather than an import, so neither repo needs
the other installed.

Why bother reproducing a published table
----------------------------------------
Because it is the only cheap check that the whole pipeline is right. DHS
published India's NFHS-5 stunting rate as 35.5 percent, and 46.1 percent in the
poorest wealth quintile falling to 22.9 in the richest. If your run does not
land within a few tenths of that, something upstream is wrong, and the usual
suspects are an unscaled weight, a domain filtered before estimation, or an
anthropometry flag kept as though it were a measurement.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from survey_estimation.design_based_estimates import svy_prop_by, compare_to_published

# DHS Program API, indicator CN_NUTS_C_HA2 (children stunted, height-for-age
# below -2 SD of the WHO 2006 median), survey IA2020DHS, retrieved 2026-09-08.
PUBLISHED_NFHS5 = pd.DataFrame({
    "wealth_quintile": ["Lowest", "Second", "Middle", "Fourth", "Highest", "Total"],
    "published": [46.1, 39.7, 34.4, 28.1, 22.9, 35.5],
})

QUINTILE_LABELS = {1: "Lowest", 2: "Second", 3: "Middle", 4: "Fourth", 5: "Highest"}


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Build the stunting indicator and the wealth quintile labels.

    Two filters matter and neither announces itself if you skip it. The
    children's recode covers births in the last five years including children
    who have died, so `b5 == 1` is required before any anthropometry. And a
    child with no valid height-for-age is not a child who is not stunted; those
    rows carry a missing outcome, which the estimator keeps in the design and
    out of the numerator.
    """
    if "haz" not in df.columns:
        raise KeyError(
            "No 'haz' column. Run the loader with --anthro so the flags at 9990 "
            "and above are dropped before the values are divided by 100."
        )
    out = df.copy()

    if "b5" in out.columns:
        before = len(out)
        out = out[out["b5"] == 1]
        print(f"  living children: {len(out):,} of {before:,}", file=sys.stderr)

    out["stunted"] = np.where(out["haz"].notna(), (out["haz"] < -2).astype(float), np.nan)
    measured = int(out["stunted"].notna().sum())
    print(f"  with a valid height-for-age: {measured:,} of {len(out):,}", file=sys.stderr)

    if "v190" in out.columns:
        out["wealth_quintile"] = out["v190"].map(QUINTILE_LABELS)
    return out


def stunting_by_wealth(df: pd.DataFrame) -> pd.DataFrame:
    """Stunting prevalence by wealth quintile, with design-based intervals."""
    est = svy_prop_by(df, "stunted", by="wealth_quintile")
    order = ["Lowest", "Second", "Middle", "Fourth", "Highest", "Total"]
    est["wealth_quintile"] = pd.Categorical(est["wealth_quintile"], order, ordered=True)
    return est.sort_values("wealth_quintile").reset_index(drop=True)


def report(est: pd.DataFrame, published: pd.DataFrame | None = PUBLISHED_NFHS5,
           tolerance: float = 0.5) -> pd.DataFrame:
    """Print the estimates, and the comparison when a published table is given."""
    show = est.copy()
    for col in ("estimate", "ci_low", "ci_high"):
        show[col] = (show[col] * 100).round(1)
    show["se"] = (show["se"] * 100).round(2)
    print("\nStunting by wealth quintile, percent")
    print(show[["wealth_quintile", "estimate", "se", "ci_low", "ci_high",
                "n", "n_clusters", "deff"]].to_string(index=False))

    if published is None:
        return show
    cmp = compare_to_published(est, published, on="wealth_quintile", tolerance=tolerance)
    print(f"\nAgainst the published NFHS-5 table (tolerance {tolerance} points)")
    print(cmp.round(2).to_string(index=False))
    off = cmp[~cmp["within_tolerance"].fillna(False)]
    if len(off):
        print(f"\n{len(off)} row(s) outside tolerance. Check the weight scaling, "
              "whether the subgroup was filtered before estimation, and whether "
              "the anthropometry flags were dropped before dividing by 100.",
              file=sys.stderr)
    else:
        print("\nEvery row reproduces the published figure. The pipeline is sound.")
    return cmp


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", help="Cleaned children's recode, from InsightStack's load_dhs")
    p.add_argument("--no-benchmark", action="store_true",
                   help="Skip the comparison, for a survey other than NFHS-5")
    p.add_argument("--tolerance", type=float, default=0.5,
                   help="Allowed gap in percentage points (default 0.5)")
    a = p.parse_args(argv)

    df = prepare(pd.read_csv(a.csv))
    est = stunting_by_wealth(df)
    report(est, None if a.no_benchmark else PUBLISHED_NFHS5, a.tolerance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

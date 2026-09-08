"""
Tests for survey_estimation.design_based_estimates.

A variance estimator cannot be checked by eye, so each test here pins it to a
case where the right answer is known in closed form.
"""

import numpy as np
import pandas as pd

from survey_estimation.design_based_estimates import (
    svy_prop, svy_prop_by, compare_to_published,
)


def test_point_estimate_is_the_weighted_mean():
    df = pd.DataFrame({"y": [1, 0, 1, 0], "weight": [1.0, 3.0, 1.0, 5.0],
                       "psu": [1, 2, 3, 4], "strata": [1, 1, 1, 1]})
    expected = (1 * 1 + 0 * 3 + 1 * 1 + 0 * 5) / (1 + 3 + 1 + 5)
    assert abs(svy_prop(df, "y")["estimate"] - expected) < 1e-12


def test_one_unit_per_cluster_reduces_to_the_simple_random_sample_se():
    """With one unit per PSU, one stratum and equal weights, the ultimate
    cluster estimator must collapse to s / sqrt(n)."""
    rng = np.random.default_rng(11)
    y = rng.integers(0, 2, 40).astype(float)
    df = pd.DataFrame({"y": y, "weight": np.ones(40),
                       "psu": np.arange(40), "strata": np.ones(40)})
    expected_se = y.std(ddof=1) / np.sqrt(len(y))
    assert abs(svy_prop(df, "y", ci="linear")["se"] - expected_se) < 1e-12


def test_standard_error_is_invariant_to_the_weight_scale():
    """A ratio estimator does not care whether weights are raw DHS integers or
    divided by a million. If the SE moves, the estimator is wrong."""
    rng = np.random.default_rng(7)
    n = 200
    df = pd.DataFrame({
        "y": rng.integers(0, 2, n).astype(float),
        "weight": rng.uniform(0.4, 2.5, n),
        "psu": rng.integers(0, 25, n),
        "strata": rng.integers(0, 5, n),
    })
    base = svy_prop(df, "y")
    scaled = svy_prop(df.assign(weight=df["weight"] * 1_000_000), "y")
    assert abs(base["estimate"] - scaled["estimate"]) < 1e-12
    assert abs(base["se"] - scaled["se"]) < 1e-12


def test_perfect_intracluster_correlation_gives_the_known_design_effect():
    """Every unit inside a cluster identical means rho = 1, and the design
    effect is then exactly (N - 1) / (n - 1): the sample carries only as much
    information as its cluster count."""
    n_clusters, size = 20, 5
    rng = np.random.default_rng(3)
    cluster_value = rng.integers(0, 2, n_clusters).astype(float)
    df = pd.DataFrame({
        "y": np.repeat(cluster_value, size),
        "weight": np.ones(n_clusters * size),
        "psu": np.repeat(np.arange(n_clusters), size),
        "strata": np.ones(n_clusters * size),
    })
    res = svy_prop(df, "y")
    n_total = n_clusters * size
    expected_deff = (n_total - 1) / (n_clusters - 1)
    assert abs(res["deff"] - expected_deff) < 1e-9
    # And the clustered SE must exceed the SE that ignores the design.
    naive_se = np.sqrt(res["estimate"] * (1 - res["estimate"]) / (n_total - 1))
    assert res["se"] > naive_se


def test_a_subgroup_keeps_the_clusters_that_contain_none_of_it():
    """Filtering before estimating throws away PSUs that are part of the design,
    which shrinks the standard error. Passing a domain keeps them."""
    rng = np.random.default_rng(5)
    n = 300
    df = pd.DataFrame({
        "y": rng.integers(0, 2, n).astype(float),
        "group": rng.integers(0, 5, n),
        "weight": rng.uniform(0.5, 2.0, n),
        "psu": rng.integers(0, 30, n),
        "strata": rng.integers(0, 3, n),
    })
    domain = df["group"] == 0
    correct = svy_prop(df, "y", domain=domain)
    naive = svy_prop(df[domain].copy(), "y")

    assert correct["estimate"] == naive["estimate"]      # same point estimate
    assert correct["n_clusters"] > naive["n_clusters"]   # more clusters retained
    assert correct["df"] > naive["df"]
    assert correct["se"] != naive["se"]


def test_a_stratum_with_one_cluster_does_not_crash():
    df = pd.DataFrame({
        "y": [1.0, 0.0, 1.0, 1.0, 0.0],
        "weight": [1.0] * 5,
        "psu": [1, 2, 3, 4, 9],
        "strata": [1, 1, 1, 1, 2],   # stratum 2 holds a single PSU
    })
    centered = svy_prop(df, "y", singleunit="centered")
    certainty = svy_prop(df, "y", singleunit="certainty")
    assert np.isfinite(centered["se"]) and np.isfinite(certainty["se"])
    assert certainty["se"] < centered["se"]   # a certainty unit adds no variance


def test_logit_interval_stays_inside_the_unit_interval():
    """Near zero a linear interval goes negative, which is not a proportion."""
    n = 400
    rng = np.random.default_rng(2)
    psu = rng.integers(0, 40, n)
    # A rare outcome concentrated inside a single cluster: p is 2.5% and the
    # design standard error is the same size, so the linear interval crosses zero.
    y = np.zeros(n)
    y[psu == 0] = 1.0
    df = pd.DataFrame({"y": y, "weight": np.ones(n), "psu": psu,
                       "strata": np.ones(n)})
    logit = svy_prop(df, "y", ci="logit")
    linear = svy_prop(df, "y", ci="linear")
    assert logit["ci_low"] > 0
    assert logit["ci_high"] < 1
    assert linear["ci_low"] < 0        # the reason logit is the default


def test_missing_outcomes_leave_the_estimate_but_keep_the_design():
    rng = np.random.default_rng(13)
    n = 150
    y = rng.integers(0, 2, n).astype(float)
    y[::10] = np.nan
    df = pd.DataFrame({"y": y, "weight": np.ones(n),
                       "psu": rng.integers(0, 20, n),
                       "strata": np.ones(n)})
    res = svy_prop(df, "y")
    assert res["n"] == int(np.isfinite(y).sum())
    assert res["n_clusters"] == df.groupby(["strata", "psu"]).ngroups


def test_by_returns_one_row_per_level_plus_a_total():
    rng = np.random.default_rng(17)
    n = 240
    df = pd.DataFrame({
        "y": rng.integers(0, 2, n).astype(float),
        "quintile": rng.integers(1, 6, n),
        "weight": rng.uniform(0.5, 2.0, n),
        "psu": rng.integers(0, 24, n),
        "strata": rng.integers(0, 4, n),
    })
    out = svy_prop_by(df, "y", by="quintile")
    assert len(out) == 6                       # five quintiles and a total
    assert out["quintile"].iloc[-1] == "Total"
    assert (out["ci_low"] <= out["estimate"]).all()
    assert (out["estimate"] <= out["ci_high"]).all()


def test_comparison_against_a_published_table_flags_the_gap():
    est = pd.DataFrame({"quintile": ["Lowest", "Highest"], "estimate": [0.461, 0.300]})
    pub = pd.DataFrame({"quintile": ["Lowest", "Highest"], "published": [46.1, 22.9]})
    out = compare_to_published(est, pub, on="quintile", tolerance=1.0)
    assert bool(out.loc[out["quintile"] == "Lowest", "within_tolerance"].iloc[0])
    assert not bool(out.loc[out["quintile"] == "Highest", "within_tolerance"].iloc[0])
    assert abs(out.loc[out["quintile"] == "Highest", "difference"].iloc[0] - 7.1) < 1e-9


def test_the_interval_records_which_distribution_produced_it():
    """A survey design has finite degrees of freedom. Where the t quantile is
    unavailable the result must say so rather than quietly using 1.96."""
    rng = np.random.default_rng(23)
    n = 200
    df = pd.DataFrame({"y": rng.integers(0, 2, n).astype(float),
                       "weight": np.ones(n),
                       "psu": rng.integers(0, 20, n),
                       "strata": np.ones(n)})
    res = svy_prop(df, "y")
    assert "ci_dist" in res
    assert res["ci_dist"].startswith("t(") or "scipy absent" in res["ci_dist"]


def test_a_non_default_confidence_level_is_honoured():
    """The old fallback hardcoded the 95 percent quantile, so a 99 percent
    interval came back at 95 percent width with nothing to show for it."""
    rng = np.random.default_rng(29)
    n = 300
    df = pd.DataFrame({"y": rng.integers(0, 2, n).astype(float),
                       "weight": np.ones(n),
                       "psu": rng.integers(0, 30, n),
                       "strata": np.ones(n)})
    narrow = svy_prop(df, "y", conf=0.90, ci="linear")
    wide = svy_prop(df, "y", conf=0.99, ci="linear")
    assert (wide["ci_high"] - wide["ci_low"]) > (narrow["ci_high"] - narrow["ci_low"])


def test_the_documented_top_level_import_works():
    """The README shows `from survey_estimation import svy_prop_by`, so the
    package has to re-export it."""
    import survey_estimation

    assert callable(survey_estimation.svy_prop_by)
    assert callable(survey_estimation.svy_prop)
    assert callable(survey_estimation.compare_to_published)

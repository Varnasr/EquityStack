"""Tests for social_sector.composite_index.

The failure mode a composite index has is not an exception, it is a ranking
that looks authoritative and would have come out differently under an equally
defensible choice. So these tests check the choices bite: that direction flips
the contribution, that weights move the answer by the amount they should, that
a row with two of six indicators does not quietly score near the top, and that
`rank_sensitivity` actually reports movement when movement exists.
"""

import numpy as np
import pandas as pd
import pytest

from social_sector.composite_index import composite_index, normalise, rank_sensitivity


@pytest.fixture
def districts():
    return pd.DataFrame({
        "district": list("ABCDE"),
        "imm_pct": [95.0, 80.0, 60.0, 40.0, 20.0],
        "imr": [12.0, 20.0, 35.0, 50.0, 70.0],       # lower is better
        "piped_pct": [90.0, 70.0, 50.0, 30.0, 5.0],
    })


# --------------------------------------------------------------------------
# normalise
# --------------------------------------------------------------------------

def test_minmax_puts_the_extremes_at_zero_and_one():
    out = normalise([10.0, 20.0, 30.0])
    assert out.tolist() == pytest.approx([0.0, 0.5, 1.0])


def test_lower_is_better_flips_the_scale():
    out = normalise([10.0, 20.0, 30.0], direction="lower_is_better")
    assert out.tolist() == pytest.approx([1.0, 0.5, 0.0])


def test_zscore_lower_is_better_negates_rather_than_subtracting_from_one():
    """1 - z would shift the mean to 1; a z-score's neutral point is 0."""
    out = normalise([10.0, 20.0, 30.0], method="zscore", direction="lower_is_better")
    assert out.mean() == pytest.approx(0.0)
    assert out.iloc[0] > 0 and out.iloc[-1] < 0


def test_goalposts_do_not_depend_on_the_sample():
    a = normalise([40.0, 60.0], method="goalpost", goalposts=(0, 100))
    b = normalise([40.0, 60.0, 95.0], method="goalpost", goalposts=(0, 100))
    assert a.tolist() == pytest.approx(b.iloc[:2].tolist())
    assert a.tolist() == pytest.approx([0.4, 0.6])


def test_minmax_does_depend_on_the_sample_which_is_why_goalposts_exist():
    a = normalise([40.0, 60.0])
    b = normalise([40.0, 60.0, 95.0])
    assert a.tolist() != pytest.approx(b.iloc[:2].tolist())


def test_goalpost_without_goalposts_refuses():
    with pytest.raises(ValueError, match="needs explicit goalposts"):
        normalise([1.0, 2.0], method="goalpost")


def test_a_constant_indicator_becomes_the_midpoint_not_a_division_by_zero():
    out = normalise([7.0, 7.0, 7.0])
    assert out.tolist() == [0.5, 0.5, 0.5]


def test_missing_stays_missing():
    out = normalise([1.0, np.nan, 3.0])
    assert np.isnan(out.iloc[1])
    assert out.iloc[0] == 0.0 and out.iloc[2] == 1.0


# --------------------------------------------------------------------------
# composite_index
# --------------------------------------------------------------------------

def test_direction_is_applied_so_a_mortality_rate_does_not_cancel_coverage(districts):
    """Without the direction argument, imm_pct and imr pull against each other."""
    right = composite_index(districts, ["imm_pct", "imr"],
                            directions={"imr": "lower_is_better"})
    wrong = composite_index(districts, ["imm_pct", "imr"])

    # Expected computed from the definition rather than pasted: min-max each
    # column over its own observed range, flip the mortality rate, average.
    imm = districts["imm_pct"]
    imr = districts["imr"]
    a = (imm - imm.min()) / (imm.max() - imm.min())
    b = 1.0 - (imr - imr.min()) / (imr.max() - imr.min())
    assert right["index"].tolist() == pytest.approx(((a + b) / 2).tolist())

    # Left as higher-is-better the two indicators pull against each other and
    # very nearly cancel, which is the bug the direction argument exists to stop.
    assert wrong["index"].std() < 0.1 * right["index"].std()


def test_weights_are_rescaled_to_sum_to_one(districts):
    a = composite_index(districts, ["imm_pct", "piped_pct"],
                        weights={"imm_pct": 3, "piped_pct": 1})
    b = composite_index(districts, ["imm_pct", "piped_pct"],
                        weights={"imm_pct": 0.75, "piped_pct": 0.25})
    assert a["index"].tolist() == pytest.approx(b["index"].tolist())
    assert a.attrs["composite_index"]["weights"]["imm_pct"] == pytest.approx(0.75)


def test_unnamed_indicators_split_the_residual_weight(districts):
    r = composite_index(districts, ["imm_pct", "imr", "piped_pct"],
                        weights={"imm_pct": 0.5},
                        directions={"imr": "lower_is_better"})
    w = r.attrs["composite_index"]["weights"]
    assert w["imm_pct"] == pytest.approx(0.5)
    assert w["imr"] == pytest.approx(0.25)
    assert w["piped_pct"] == pytest.approx(0.25)


def test_weights_that_leave_no_residual_refuse(districts):
    with pytest.raises(ValueError, match="leaving\nnothing|leaving nothing"):
        composite_index(districts, ["imm_pct", "imr", "piped_pct"],
                        weights={"imm_pct": 0.6, "imr": 0.4},
                        directions={"imr": "lower_is_better"})


def test_geometric_punishes_a_near_zero_where_arithmetic_averages_it_away():
    df = pd.DataFrame({
        "u": ["balanced", "lopsided"],
        "a": [0.5, 1.0],
        "b": [0.5, 0.0],
    })
    ari = composite_index(df, ["a", "b"], method="goalpost",
                          goalposts={"a": (0, 1), "b": (0, 1)})
    geo = composite_index(df, ["a", "b"], method="goalpost", aggregation="geometric",
                          goalposts={"a": (0, 1), "b": (0, 1)})
    # arithmetic scores them equally; geometric does not
    assert ari["index"].iloc[0] == pytest.approx(ari["index"].iloc[1])
    assert geo["index"].iloc[0] > geo["index"].iloc[1]


def test_geometric_refuses_z_scores(districts):
    with pytest.raises(ValueError, match="geometric mean of z-scores"):
        composite_index(districts, ["imm_pct", "piped_pct"],
                        method="zscore", aggregation="geometric")


def test_a_row_scored_on_two_of_six_indicators_is_refused_by_default():
    df = pd.DataFrame({
        "u": ["complete", "sparse"],
        "a": [0.5, 1.0], "b": [0.5, 1.0], "c": [0.5, np.nan],
        "d": [0.5, np.nan], "e": [0.5, np.nan], "f": [0.5, np.nan],
    })
    cols = list("abcdef")
    strict = composite_index(df, cols)
    assert not np.isnan(strict["index"].iloc[0])
    assert np.isnan(strict["index"].iloc[1])          # would otherwise have topped the list

    lenient = composite_index(df, cols, min_indicators=2)
    assert not np.isnan(lenient["index"].iloc[1])
    assert lenient["index_n_indicators"].tolist() == [6, 2]


def test_present_indicators_are_reweighted_so_a_gap_does_not_score_as_a_zero():
    df = pd.DataFrame({"a": [1.0, 1.0], "b": [1.0, np.nan], "c": [1.0, 1.0]})
    r = composite_index(df, ["a", "b", "c"], method="goalpost", min_indicators=2,
                        goalposts={c: (0, 1) for c in "abc"})
    assert r["index"].tolist() == pytest.approx([1.0, 1.0])


def test_choices_are_recorded_on_the_result(districts):
    r = composite_index(districts, ["imm_pct", "imr"],
                        directions={"imr": "lower_is_better"}, method="rank")
    meta = r.attrs["composite_index"]
    assert meta["method"] == "rank"
    assert meta["directions"] == {"imr": "lower_is_better"}
    assert meta["indicators"] == ["imm_pct", "imr"]


def test_a_typo_in_directions_raises_rather_than_being_ignored(districts):
    with pytest.raises(KeyError, match="directions names column"):
        composite_index(districts, ["imm_pct", "imr"], directions={"IMR": "lower_is_better"})


def test_one_indicator_is_not_an_index(districts):
    with pytest.raises(ValueError, match="not an index"):
        composite_index(districts, ["imm_pct"])


# --------------------------------------------------------------------------
# rank_sensitivity
# --------------------------------------------------------------------------

def test_sensitivity_reports_zero_spread_when_indicators_agree(districts):
    out = rank_sensitivity(districts, ["imm_pct", "imr", "piped_pct"], unit="district",
                           directions={"imr": "lower_is_better"})
    assert out["rank_spread"].max() == 0


def test_sensitivity_finds_a_district_whose_rank_depends_on_the_method():
    """One district with a huge outlier on one indicator and a poor showing on
    the other. z-score rewards the outlier's magnitude; rank throws it away."""
    df = pd.DataFrame({
        "district": ["outlier", "steady1", "steady2", "steady3", "steady4"],
        "a": [1000.0, 60.0, 55.0, 50.0, 45.0],
        "b": [1.0, 60.0, 58.0, 56.0, 54.0],
    })
    out = rank_sensitivity(df, ["a", "b"], unit="district")
    assert out["rank_spread"].max() > 0
    worst = out.iloc[0]
    assert worst["district"] == "outlier"

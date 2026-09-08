"""Tests for the inequality package.

Pinned to answers known in closed form, not to what this code happens to
return. A distributional index cannot be checked by eye: a Gini of 0.31 and a
Gini of 0.34 both look like plausible consumption inequality, and a sign error
in a concentration index produces a number in exactly the right range that says
the opposite of the truth. So every test here is either an identity the measure
must satisfy, or a figure worked out by hand from the definition.

Where a number is hardcoded, the arithmetic behind it is in the comment.
"""

import math

import numpy as np
import pandas as pd
import pytest

from inequality import (
    achievement_index, atkinson, benefit_incidence, benefit_incidence_by_level,
    concentration_curve, concentration_index, concentration_index_by,
    erreygers_index, fractional_rank, generalised_entropy, gini, lorenz_curve,
    oaxaca_blinder, palma_ratio, quantile_shares, ratio_80_20, share_of_bottom,
    share_of_top, theil_decomposition, theil_l, theil_t, wagstaff_index,
    weighted_quantile,
)

# --------------------------------------------------------------------------
# Fractional ranks
# --------------------------------------------------------------------------

def test_mean_fractional_rank_is_exactly_one_half():
    """The proof of CI = 2·cov(h,r)/h̄ needs r̄ = 0.5. It holds for any weights."""
    rng = np.random.default_rng(0)
    for _ in range(20):
        n = rng.integers(2, 60)
        x = rng.normal(size=n)
        w = rng.gamma(2.0, 1.0, size=n)
        r = fractional_rank(x, w)
        assert np.isclose(np.sum(w * r) / np.sum(w), 0.5)


def test_ties_share_the_block_midpoint():
    # values 1,1,2 with unit weights: the pair occupies [0, 2/3], midpoint 1/3;
    # the single occupies [2/3, 1], midpoint 5/6.
    assert np.allclose(fractional_rank([1, 1, 2]), [1 / 3, 1 / 3, 5 / 6])


def test_rank_does_not_depend_on_row_order():
    x = [3, 1, 2, 1, 3]
    r1 = fractional_rank(x)
    order = [4, 0, 3, 2, 1]
    r2 = fractional_rank([x[i] for i in order])
    assert np.allclose(sorted(r1), sorted(r2))


def test_missing_values_rank_as_nan_not_as_poorest():
    r = fractional_rank([1.0, np.nan, 3.0])
    assert math.isnan(r[1])
    assert np.allclose(r[[0, 2]], [0.25, 0.75])


# --------------------------------------------------------------------------
# Gini
# --------------------------------------------------------------------------

def test_gini_matches_hand_computed_mean_difference():
    # y = 1..5. Sum of |yi - yj| over ordered pairs = 40, n^2 = 25, so the mean
    # absolute difference is 1.6 and G = 1.6 / (2 * 3) = 0.2666...
    assert gini([1, 2, 3, 4, 5]) == pytest.approx(4 / 15)


def test_gini_equals_mean_difference_formula_on_random_data():
    rng = np.random.default_rng(3)
    for _ in range(15):
        y = rng.gamma(2.0, 3.0, size=rng.integers(3, 40))
        mad = np.abs(y[:, None] - y[None, :]).mean()
        assert gini(y) == pytest.approx(mad / (2 * y.mean()))


def test_gini_is_zero_at_equality_and_one_in_the_limit():
    assert gini([7, 7, 7, 7]) == pytest.approx(0.0, abs=1e-12)
    # one person holds everything, n large: G -> 1 - 1/n
    n = 1000
    y = np.zeros(n); y[-1] = 1.0
    assert gini(y) == pytest.approx(1 - 1 / n, abs=1e-9)


def test_gini_is_scale_invariant():
    y = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0]
    assert gini(y) == pytest.approx(gini(np.array(y) * 137.0))


def test_a_weight_of_two_equals_the_row_appearing_twice():
    assert gini([1, 2], weights=[2, 1]) == pytest.approx(gini([1, 1, 2]))
    assert theil_t([1, 2], weights=[2, 1]) == pytest.approx(theil_t([1, 1, 2]))
    assert atkinson([1, 2], weights=[2, 1]) == pytest.approx(atkinson([1, 1, 2]))


def test_gini_rejects_negative_values_rather_than_returning_a_number():
    with pytest.raises(ValueError, match="negative"):
        gini([-1.0, 2.0, 3.0])


def test_small_sample_correction_is_the_n_over_n_minus_one_factor():
    y = [1, 2, 3, 4, 5]
    assert gini(y, small_sample_correction=True) == pytest.approx(gini(y) * 5 / 4)


# --------------------------------------------------------------------------
# Lorenz curve, shares
# --------------------------------------------------------------------------

def test_lorenz_area_reproduces_the_gini():
    rng = np.random.default_rng(11)
    y = rng.gamma(2.0, 5.0, size=200)
    w = rng.gamma(3.0, 1.0, size=200)
    curve = lorenz_curve(y, w)
    area = np.trapezoid(curve["value_share"], curve["population_share"])
    assert 2 * (0.5 - area) == pytest.approx(gini(y, w), abs=1e-9)


def test_lorenz_starts_at_origin_and_ends_at_one():
    c = lorenz_curve([4, 1, 9, 2])
    assert c.iloc[0].tolist() == [0.0, 0.0]
    assert c.iloc[-1]["population_share"] == pytest.approx(1.0)
    assert c.iloc[-1]["value_share"] == pytest.approx(1.0)


def test_quantile_shares_sum_to_one_with_awkward_weights():
    rng = np.random.default_rng(5)
    y = rng.gamma(2.0, 1.0, size=37)
    w = rng.gamma(1.0, 4.0, size=37)          # nothing divides evenly by five
    q = quantile_shares(y, w, q=5)
    assert q["value_share"].sum() == pytest.approx(1.0)
    assert len(q) == 5


def test_shares_at_perfect_equality_equal_the_population_share():
    y = [12.0] * 50
    assert share_of_top(y, p=0.10) == pytest.approx(0.10)
    assert share_of_bottom(y, p=0.40) == pytest.approx(0.40)
    assert palma_ratio(y) == pytest.approx(0.25)
    assert ratio_80_20(y) == pytest.approx(1.0)


def test_palma_rises_when_the_top_pulls_away():
    base = list(range(1, 101))
    pulled = base[:-1] + [500]
    assert palma_ratio(pulled) > palma_ratio(base)


def test_weighted_quantile_is_consistent_with_the_rank_definition():
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    # midpoint ranks are 0.1, 0.3, 0.5, 0.7, 0.9
    assert weighted_quantile(y, 0.5) == pytest.approx(3.0)
    assert weighted_quantile(y, 0.3) == pytest.approx(2.0)


# --------------------------------------------------------------------------
# Generalised entropy, Theil, Atkinson
# --------------------------------------------------------------------------

def test_ge2_is_half_the_squared_coefficient_of_variation():
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    cv2 = (y.std() / y.mean()) ** 2
    assert generalised_entropy(y, alpha=2.0) == pytest.approx(0.5 * cv2)


def test_every_index_is_zero_at_perfect_equality():
    y = [6.0] * 12
    assert theil_t(y) == pytest.approx(0.0, abs=1e-12)
    assert theil_l(y) == pytest.approx(0.0, abs=1e-12)
    assert atkinson(y, epsilon=2.0) == pytest.approx(0.0, abs=1e-12)
    assert generalised_entropy(y, alpha=2.0) == pytest.approx(0.0, abs=1e-12)


def test_atkinson_is_zero_at_no_aversion_and_rises_with_it():
    y = [1.0, 2.0, 3.0, 10.0]
    assert atkinson(y, epsilon=0.0) == 0.0
    values = [atkinson(y, epsilon=e) for e in (0.0, 0.5, 1.0, 1.5, 2.0)]
    assert all(b >= a for a, b in zip(values, values[1:]))


def test_atkinson_at_epsilon_one_is_one_minus_the_geometric_over_arithmetic_mean():
    y = np.array([1.0, 4.0, 16.0])
    expected = 1 - np.exp(np.log(y).mean()) / y.mean()
    assert atkinson(y, epsilon=1.0) == pytest.approx(expected)


def test_indices_are_scale_invariant():
    rng = np.random.default_rng(13)
    y = rng.gamma(2.0, 2.0, size=50)
    for fn in (theil_t, theil_l, lambda v: atkinson(v, epsilon=1.5)):
        assert fn(y) == pytest.approx(fn(y * 1000.0))


def test_ge_below_one_refuses_zeros_instead_of_returning_inf():
    with pytest.raises(ValueError, match="undefined"):
        generalised_entropy([0.0, 1.0, 2.0], alpha=0.0)
    with pytest.raises(ValueError, match="epsilon"):
        atkinson([0.0, 1.0, 2.0], epsilon=1.0)


# --------------------------------------------------------------------------
# Concentration index
# --------------------------------------------------------------------------

def test_concentration_index_hand_computed():
    # outcome on the poorest of four equal-weight people. Ranks 0.125, 0.375,
    # 0.625, 0.875; mean outcome 0.25.
    # CI = 2 * (1*0.125) / (4 * 0.25) - 1 = 0.25 - 1 = -0.75
    assert concentration_index([1, 0, 0, 0], rank_by=[1, 2, 3, 4]) == pytest.approx(-0.75)
    assert concentration_index([0, 0, 0, 1], rank_by=[1, 2, 3, 4]) == pytest.approx(0.75)


def test_concentration_index_is_zero_when_the_outcome_is_flat():
    assert concentration_index([1, 1, 1, 1], rank_by=[4, 3, 2, 1]) == pytest.approx(0.0, abs=1e-12)


def test_concentration_index_depends_only_on_the_rank_order_not_the_values():
    out = [0.2, 0.5, 0.1, 0.9]
    a = concentration_index(out, rank_by=[1, 2, 3, 4])
    b = concentration_index(out, rank_by=[10, 250, 3000, 99999])
    assert a == pytest.approx(b)


def test_concentration_index_is_scale_invariant_in_the_outcome():
    out = np.array([0.2, 0.5, 0.1, 0.9])
    r = [1, 2, 3, 4]
    assert concentration_index(out, r) == pytest.approx(concentration_index(out * 77.0, r))


def test_reversing_the_rank_flips_the_sign():
    out = [0.9, 0.4, 0.3, 0.05]
    assert (concentration_index(out, rank_by=[1, 2, 3, 4])
            == pytest.approx(-concentration_index(out, rank_by=[4, 3, 2, 1])))


def test_concentration_curve_area_reproduces_the_index():
    rng = np.random.default_rng(21)
    n = 300
    rank = rng.uniform(size=n)
    outcome = rng.binomial(1, np.clip(0.7 - 0.5 * rank, 0, 1)).astype(float)
    w = rng.gamma(2.0, 1.0, size=n)
    curve = concentration_curve(outcome, rank, w)
    area = np.trapezoid(curve["outcome_share"], curve["population_share"])
    assert 2 * (0.5 - area) == pytest.approx(concentration_index(outcome, rank, w), abs=1e-9)


def test_erreygers_is_four_mu_ci_for_a_binary_outcome():
    out = [1, 1, 0, 0, 0, 0, 1, 0]
    rank = [1, 2, 3, 4, 5, 6, 7, 8]
    mu = np.mean(out)
    assert erreygers_index(out, rank) == pytest.approx(4 * mu * concentration_index(out, rank))


def test_erreygers_refuses_bounds_the_data_breaks():
    with pytest.raises(ValueError, match="outside the stated"):
        erreygers_index([0, 1, 5], rank_by=[1, 2, 3], bounds=(0, 1))


def test_wagstaff_normalisation_divides_by_one_minus_the_mean():
    out = [1, 0, 0, 0]
    rank = [1, 2, 3, 4]
    assert wagstaff_index(out, rank) == pytest.approx(concentration_index(out, rank) / (1 - 0.25))


def test_wagstaff_refuses_when_everybody_has_the_outcome():
    with pytest.raises(ValueError, match="upper bound"):
        wagstaff_index([1, 1, 1, 1], rank_by=[1, 2, 3, 4])


def test_ranking_by_a_quintile_gives_the_same_sign_as_ranking_by_the_continuous_measure():
    rng = np.random.default_rng(31)
    n = 2000
    wealth = rng.normal(size=n)
    quintile = pd.qcut(wealth, 5, labels=False) + 1
    stunted = rng.binomial(1, 1 / (1 + np.exp(1.2 * wealth))).astype(float)
    fine = concentration_index(stunted, wealth)
    coarse = concentration_index(stunted, quintile)
    assert fine < 0 and coarse < 0
    # the quintile throws away within-quintile ordering, so it attenuates
    assert abs(coarse) < abs(fine)


def test_concentration_index_by_reports_rather_than_drops_a_degenerate_group():
    df = pd.DataFrame({
        "stunted": [1, 0, 1, 0, 0, 0],
        "wealth": [1, 2, 3, 4, 2, 2],
        "state": ["A", "A", "A", "A", "B", "B"],
    })
    out = concentration_index_by(df, "stunted", "wealth", by="state")
    assert set(out["state"]) == {"A", "B"}
    b = out.loc[out["state"] == "B"].iloc[0]
    assert math.isnan(b["concentration_index"])
    assert b["note"]


def test_achievement_index_discounts_a_pro_rich_distribution():
    pro_poor = [1, 1, 0, 0]
    pro_rich = [0, 0, 1, 1]
    rank = [1, 2, 3, 4]
    assert np.mean(pro_poor) == np.mean(pro_rich)          # same headline coverage
    assert achievement_index(pro_poor, rank) > achievement_index(pro_rich, rank)


# --------------------------------------------------------------------------
# Decompositions
# --------------------------------------------------------------------------

@pytest.mark.parametrize("alpha", [0.0, 1.0])
def test_theil_within_plus_between_equals_total(alpha):
    rng = np.random.default_rng(41)
    n = 300
    y = rng.gamma(2.0, 3.0, size=n)
    g = rng.integers(0, 5, size=n)
    w = rng.gamma(2.0, 1.0, size=n)
    d = theil_decomposition(y, g, w, alpha=alpha)
    assert d["within"] + d["between"] == pytest.approx(d["total"])


def test_between_is_zero_when_groups_have_the_same_distribution():
    d = theil_decomposition([1, 2, 3, 1, 2, 3], ["a"] * 3 + ["b"] * 3)
    assert d["between"] == pytest.approx(0.0, abs=1e-12)


def test_within_is_zero_when_each_group_is_internally_equal():
    d = theil_decomposition([1, 1, 1, 5, 5, 5], ["a"] * 3 + ["b"] * 3)
    assert d["within"] == pytest.approx(0.0, abs=1e-12)
    assert d["between_share"] == pytest.approx(1.0)


def test_theil_decomposition_refuses_an_alpha_that_does_not_decompose():
    with pytest.raises(ValueError, match="does not decompose"):
        theil_decomposition([1, 2, 3], ["a", "a", "b"], alpha=2.0)


def _oaxaca_frame(seed, beta_a, beta_b, mean_a=8.0, mean_b=5.0, n=400):
    rng = np.random.default_rng(seed)
    edu = np.concatenate([rng.normal(mean_a, 2, n), rng.normal(mean_b, 2, n)])
    grp = np.array(["other"] * n + ["st"] * n)
    coef = np.where(grp == "other", beta_a, beta_b)
    y = 1.0 + coef * edu + rng.normal(0, 0.05, 2 * n)
    return pd.DataFrame({"y": y, "edu": edu, "g": grp})


def test_oaxaca_components_sum_to_the_gap():
    df = _oaxaca_frame(51, 0.5, 0.3)
    for ref in ("pooled", "advantaged", "disadvantaged"):
        r = oaxaca_blinder(df, "y", "g", ["edu"], reference=ref)
        assert r["explained"] + r["unexplained"] == pytest.approx(r["gap"])
    r3 = oaxaca_blinder(df, "y", "g", ["edu"], reference="threefold")
    assert (r3["endowments"] + r3["coefficients"] + r3["interaction"]
            == pytest.approx(r3["gap"]))


def test_oaxaca_unexplained_vanishes_when_the_returns_are_identical():
    df = _oaxaca_frame(52, 0.5, 0.5)
    r = oaxaca_blinder(df, "y", "g", ["edu"], reference="pooled")
    assert abs(r["unexplained"]) < 0.02 * abs(r["gap"])


def test_oaxaca_explained_vanishes_when_the_endowments_are_identical():
    """Identical *realised* endowments, not merely the same drawing distribution.

    Drawing both groups from N(6, 2) leaves a sampling difference in the means
    of order 0.14 at n = 400, which the explained component correctly picks up:
    it is a real difference in this sample's endowments. So the two groups get
    the same education vector, and then the explained part must be zero to
    machine precision rather than merely small.
    """
    rng = np.random.default_rng(53)
    edu = rng.normal(6.0, 2.0, 400)
    df = pd.DataFrame({
        "edu": np.concatenate([edu, edu]),
        "g": np.array(["other"] * 400 + ["st"] * 400),
        "y": np.concatenate([1.0 + 0.5 * edu, 1.0 + 0.3 * edu]),
    })
    r = oaxaca_blinder(df, "y", "g", ["edu"], reference="pooled")
    assert r["explained"] == pytest.approx(0.0, abs=1e-9)
    assert r["unexplained"] == pytest.approx(r["gap"])


def test_oaxaca_refuses_more_than_two_groups():
    df = _oaxaca_frame(54, 0.5, 0.3)
    df.loc[df.index[:5], "g"] = "third"
    with pytest.raises(ValueError, match="exactly two groups"):
        oaxaca_blinder(df, "y", "g", ["edu"])


def test_oaxaca_refuses_an_underidentified_group():
    df = _oaxaca_frame(55, 0.5, 0.3, n=3)
    df = pd.concat([df[df.g == "other"], df[df.g == "st"].head(1)])
    with pytest.raises(ValueError, match="not identified"):
        oaxaca_blinder(df, "y", "g", ["edu"])


# --------------------------------------------------------------------------
# Benefit incidence
# --------------------------------------------------------------------------

def test_benefit_incidence_allocates_the_whole_budget_by_utilisation_share():
    d = pd.DataFrame({"visits": [3, 2, 1, 0], "q": [1, 2, 3, 4]})
    out = benefit_incidence(d, utilisation="visits", group="q", spending=600)
    assert out["benefit"].sum() == pytest.approx(600)
    assert out["benefit"].tolist() == pytest.approx([300, 200, 100, 0])
    assert out.attrs["concentration_index"] < 0
    assert "progressive" in out.attrs["verdict"]


def test_benefit_incidence_refuses_blank_utilisation():
    d = pd.DataFrame({"visits": [3, None, 1], "q": [1, 2, 3]})
    with pytest.raises(ValueError, match="missing utilisation"):
        benefit_incidence(d, utilisation="visits", group="q", spending=100)


def test_net_benefit_subtracts_what_the_household_paid():
    d = pd.DataFrame({"visits": [1, 1], "q": [1, 2], "fee": [10.0, 90.0]})
    out = benefit_incidence(d, utilisation="visits", group="q", spending=100, fees="fee")
    assert out.sort_values("q")["net_benefit"].tolist() == pytest.approx([40.0, -40.0])


def test_level_split_reveals_what_the_aggregate_hides():
    d = pd.DataFrame({
        "u": [5, 4, 3, 2, 1, 0, 1, 2, 4, 8],
        "q": [1, 2, 3, 4, 5] * 2,
        "lvl": ["primary"] * 5 + ["tertiary"] * 5,
    })
    r = benefit_incidence_by_level(d, utilisation="u", group="q", level="lvl",
                                   spending={"primary": 1000, "tertiary": 1000})
    assert r["concentration_index_by_level"]["primary"] < 0
    assert r["concentration_index_by_level"]["tertiary"] > 0
    assert r["total"]["benefit"].sum() == pytest.approx(2000)


def test_level_split_refuses_a_level_with_no_budget():
    d = pd.DataFrame({"u": [1, 1], "q": [1, 2], "lvl": ["primary", "tertiary"]})
    with pytest.raises(ValueError, match="no budget given"):
        benefit_incidence_by_level(d, utilisation="u", group="q", level="lvl",
                                   spending={"primary": 100})


# --------------------------------------------------------------------------
# Input handling shared across the package
# --------------------------------------------------------------------------

def test_missing_rows_are_dropped_pairwise_not_treated_as_zero():
    with_gap = gini([1.0, 2.0, np.nan, 4.0])
    without = gini([1.0, 2.0, 4.0])
    assert with_gap == pytest.approx(without)


def test_negative_weights_are_refused_everywhere():
    for call in (lambda: gini([1, 2, 3], weights=[1, -1, 1]),
                 lambda: concentration_index([1, 0, 1], [1, 2, 3], weights=[1, -1, 1]),
                 lambda: theil_t([1, 2, 3], weights=[1, -1, 1])):
        with pytest.raises(ValueError, match="negative weights"):
            call()


def test_mismatched_lengths_are_refused():
    with pytest.raises(ValueError, match="rows"):
        gini([1, 2, 3], weights=[1, 1])
    with pytest.raises(ValueError, match="rows"):
        concentration_index([1, 0, 1], rank_by=[1, 2])

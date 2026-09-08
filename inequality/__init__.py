"""Distributional analysis: how unequally something is spread, and across whom.

    from inequality import gini, concentration_index, theil_decomposition

Four groups of function, and the choice between them is the choice of question.

**One variable, how unequal?**  `gini`, `theil_t`, `theil_l`, `atkinson`,
`generalised_entropy`, `palma_ratio`, `ratio_80_20`, `quantile_shares`,
`lorenz_curve`, `share_of_top`, `share_of_bottom`.

**Two variables, unequal across whom?**  `concentration_index` and its
prevalence-comparable corrections `erreygers_index` and `wagstaff_index`, plus
`concentration_curve`, `concentration_index_by` for a table by state or round,
and `achievement_index`.

**Where does it sit, and what explains a gap?**  `theil_decomposition` splits
inequality exactly into within-group and between-group parts.
`oaxaca_blinder` splits a mean gap into endowments and returns.

**Who gets the money?**  `benefit_incidence` and `benefit_incidence_by_level`.

Everything takes survey weights, drops missing rows pairwise rather than
imputing, and refuses rather than returning a plausible wrong number when the
input violates an assumption the measure depends on. Weighted fractional ranks
are shared through `ranks.fractional_rank`, so the Gini, the concentration index
and both curves agree with each other by construction.

For a standard error on any of these, resample: the analytic variance of a
concentration index under a clustered design is not something to write from
memory, and a bootstrap over PSUs within strata gets there honestly. The design
machinery is in this repository's `survey_estimation` package.
"""

from .ranks import fractional_rank, weighted_mean
from .indices import (
    gini, lorenz_curve, share_of_top, share_of_bottom, quantile_shares,
    palma_ratio, ratio_80_20, generalised_entropy, theil_t, theil_l,
    atkinson, weighted_quantile,
)
from .concentration import (
    concentration_index, erreygers_index, wagstaff_index, concentration_curve,
    concentration_index_by, achievement_index,
)
from .decomposition import theil_decomposition, oaxaca_blinder
from .incidence import benefit_incidence, benefit_incidence_by_level

__all__ = [
    "fractional_rank", "weighted_mean",
    "gini", "lorenz_curve", "share_of_top", "share_of_bottom", "quantile_shares",
    "palma_ratio", "ratio_80_20", "generalised_entropy", "theil_t", "theil_l",
    "atkinson", "weighted_quantile",
    "concentration_index", "erreygers_index", "wagstaff_index",
    "concentration_curve", "concentration_index_by", "achievement_index",
    "theil_decomposition", "oaxaca_blinder",
    "benefit_incidence", "benefit_incidence_by_level",
]

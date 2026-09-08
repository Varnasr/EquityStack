# inequality

Distributional analysis for survey microdata: how unequally something is
spread, and across whom. Every function takes optional survey weights.

```python
from inequality import gini, concentration_index, theil_decomposition

gini(df.consumption, weights=df.hh_weight)
concentration_index(df.stunted, rank_by=df.wealth_index, weights=df.child_weight)
theil_decomposition(df.consumption, groups=df.state, weights=df.hh_weight)
```

## Functions

**One variable: how unequal is it?**

| Function | Use |
| --- | --- |
| `gini` | The standard summary; comparable with most published figures |
| `theil_t`, `theil_l` | Entropy measures; the two that decompose exactly into within and between |
| `atkinson` | Inequality with a stated aversion parameter |
| `generalised_entropy` | GE(α): sensitive to the bottom (0), neutral (1) or the top (2) |
| `palma_ratio`, `ratio_80_20` | Ratios of shares, for a non-technical audience |
| `quantile_shares`, `lorenz_curve`, `share_of_top` | The distribution itself |

**Two variables: unequal across whom?**

| Function | Use |
| --- | --- |
| `concentration_index` | Is the outcome concentrated among the poor? Negative means yes |
| `erreygers_index` | Comparing the same indicator across states or years with different means, absolute version |
| `wagstaff_index` | The same, relative version. Pick one and say which |
| `concentration_curve` | For plotting, or checking dominance between two distributions |
| `concentration_index_by` | One index per group: state, round, sex |
| `achievement_index` | Level and distribution in one number. Report beside the mean |

**What explains it?**

| Function | Use |
| --- | --- |
| `theil_decomposition` | Within-group and between-group parts of total inequality |
| `oaxaca_blinder` | A group gap split into endowments and returns |

**Who gets the money?**

| Function | Use |
| --- | --- |
| `benefit_incidence` | A budget allocated across quintiles by who uses the service |
| `benefit_incidence_by_level` | The same, split by primary, secondary and tertiary |

## Notes

The concentration index ranks by living standards, not by the outcome. The
signature is `concentration_index(outcome, rank_by=...)`. Reversing them
returns a number in the right range with the wrong meaning.

Negative means concentrated among the poor. For stunting that is the expected
direction; for institutional delivery it is the good direction.

A raw concentration index is not comparable across different prevalences,
because its range shrinks as a binary outcome's mean moves away from 0.5. Use
`erreygers_index` for absolute comparisons and `wagstaff_index` for relative
ones. They can disagree about the direction of change; choose before looking
at the answer.

Ties, such as a wealth quintile, share the midpoint rank of their block. This
is the World Bank's DHS convention. The index is smaller than it would be on a
continuous wealth measure; a test checks the attenuation runs the expected
way.

## Standard errors

None of these functions returns one. Bootstrap over PSUs within strata,
resampling clusters rather than households:

```python
import numpy as np
from inequality import concentration_index

def boot_ci(df, reps=500, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(reps):
        parts = []
        for _, stratum in df.groupby("strata"):
            psus = stratum["psu"].unique()
            drawn = rng.choice(psus, size=len(psus), replace=True)
            parts.append(pd.concat([stratum[stratum.psu == p] for p in drawn]))
        rep = pd.concat(parts)
        out.append(concentration_index(rep.stunted, rep.wealth_index, rep.weight))
    return np.percentile(out, [2.5, 97.5])
```

## Tests

`tests/test_inequality.py`, 54 checks. Each is an identity the measure must
satisfy or a value worked out by hand: the Gini against the mean absolute
difference over twice the mean, computed by brute force over all pairs; twice
the area between the Lorenz curve and the diagonal against the Gini; the mean
fractional rank equal to 0.5 under any weights and ties; `within + between ==
total` for GE(0) and GE(1); Oaxaca components summing to the gap under all four
reference choices; a weight of 2 equal to a row appearing twice; GE(2) equal to
half the squared coefficient of variation.

## Sources

Cowell, *Measuring Inequality*, 3rd edn, Oxford University Press, 2011,
chapters 2 and 3.

O'Donnell, van Doorslaer, Wagstaff and Lindelow, *Analyzing Health Equity
Using Household Survey Data*, World Bank, 2008, chapters 8 and 15.

Erreygers, "Correcting the concentration index", *Journal of Health
Economics* 28(2), 2009, 504-515.

Wagstaff, "The bounds of the concentration index when the variable of
interest is binary", *Health Economics* 14(4), 2005, 429-432.

Demery, *Benefit Incidence: A Practitioner's Guide*, World Bank, 2000.

Fortin, Lemieux and Firpo, "Decomposition methods in economics", *Handbook of
Labor Economics* 4A, 2011, section 3.

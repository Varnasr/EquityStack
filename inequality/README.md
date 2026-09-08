# inequality

Distributional analysis for survey microdata: how unequally something is spread,
and across whom.

The rest of this repository answers "what is the level, and how sure are we".
This package answers the question that follows: **who has it**. Those are
different questions and the second one is the harder to get right, because every
measure of it is a covariance between an outcome and a position in a
distribution, and positions are where the errors hide.

```python
from inequality import gini, concentration_index, theil_decomposition

gini(df.consumption, weights=df.hh_weight)
concentration_index(df.stunted, rank_by=df.wealth_index, weights=df.child_weight)
theil_decomposition(df.consumption, groups=df.state, weights=df.hh_weight)
```

## What to reach for

**One variable, how unequal is it?**

| Function | Use when |
|---|---|
| `gini` | The headline. Comparable with almost every published figure. |
| `theil_t`, `theil_l` | You need the within/between split. Only GE(0) and GE(1) decompose exactly. |
| `atkinson` | You want the inequality aversion stated rather than implied. |
| `generalised_entropy` | You want to choose where the index is sensitive: GE(0) bottom, GE(1) neutral, GE(2) top. |
| `palma_ratio`, `ratio_80_20` | The audience is not technical. Both are ratios of shares. |
| `quantile_shares`, `lorenz_curve`, `share_of_top` | You want the distribution itself, not a summary of it. |

**Two variables, unequal across whom?**

| Function | Use when |
|---|---|
| `concentration_index` | The core: is this outcome concentrated among the poor? Negative means yes. |
| `erreygers_index` | Comparing the same indicator across states or years whose mean differs. |
| `wagstaff_index` | The same problem, relative rather than absolute. Pick one and say which. |
| `concentration_curve` | Plotting it, or checking dominance between two distributions. |
| `concentration_index_by` | A table: one gradient per state, per round, per sex. |
| `achievement_index` | One number combining level and distribution. Report it beside the mean, never instead. |

**What explains it?**

| Function | Use when |
|---|---|
| `theil_decomposition` | Is national inequality *between* states or *within* them? |
| `oaxaca_blinder` | How much of a group gap is endowments, how much is returns? |

**Who gets the money?**

| Function | Use when |
|---|---|
| `benefit_incidence` | Allocating a budget across quintiles by who uses the service. |
| `benefit_incidence_by_level` | The same, split by primary / secondary / tertiary, which is usually where the finding is. |

## Four things that are easy to get wrong

**The concentration index ranks by living standards, not by the outcome.**
Reversing them returns a number in the right range with the wrong meaning, and
nothing errors. The signature makes it awkward to do by accident: outcome first,
then `rank_by=`.

**Sign convention.** Negative means concentrated among the *poor*. For stunting
that is the expected direction and it is bad news; for institutional delivery it
is good news. The index has no opinion about which.

**A raw concentration index is not comparable across different prevalences.** Its
theoretical range shrinks as a binary outcome's mean moves away from 0.5, so an
indicator at 8 per cent and the same indicator at 60 per cent cannot be put in
one table without a correction. Erreygers keeps absolute gradients comparable,
Wagstaff keeps relative ones, and they can disagree about the direction of
change over time. Choose before you look at the answer.

**Ties.** A wealth quintile is a legitimate ranking variable and this package
handles it the way the World Bank's own DHS equity work does: everyone sharing a
quintile shares the midpoint rank of the block that quintile occupies. The index
is attenuated relative to a continuous wealth measure, which is a property of the
coarser data and not a defect. `test_inequality.py` asserts the attenuation runs
in the expected direction.

## Standard errors

None of these functions return one. The analytic variance of a concentration
index under a stratified clustered design is not something to write from memory,
and the convenient regression form people quote gives a standard error that
ignores the design entirely.

Bootstrap over PSUs within strata instead, resampling clusters rather than
households, and use this repository's `survey_estimation` package for the design
object. Roughly:

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

## Verification

`tests/test_inequality.py`, 54 checks. Every one is either an identity the
measure must satisfy or a figure worked out by hand from the definition, never
a number this code produced on a previous run. A distributional index cannot be
checked by eye: 0.31 and 0.34 are both plausible consumption Ginis, and a sign
error gives you a number in exactly the right range that says the opposite of
the truth.

The identities that carry the most weight:

- The Gini equals the mean absolute difference over twice the mean, on fifteen
  random datasets, computed independently by brute force over all pairs.
- Twice the area between the Lorenz curve and the diagonal equals the Gini, and
  the same for the concentration curve and the concentration index.
- The mean fractional rank is exactly 0.5 for any weights and any pattern of
  ties. Three derivations here depend on it.
- `within + between == total` in the Theil decomposition, for both GE(0) and
  GE(1), with weights.
- Oaxaca's components sum to the gap under all four reference choices.
- A weight of 2 gives the same answer as the row appearing twice.
- GE(2) equals half the squared coefficient of variation.

## Sources

Cowell, *Measuring Inequality*, 3rd edn, Oxford University Press 2011, chapters
2-3, for the entropy family and the axioms.

O'Donnell, van Doorslaer, Wagstaff and Lindelow, *Analyzing Health Equity Using
Household Survey Data*, World Bank 2008, chapters 8 and 15, for the
concentration index and its corrections.

Erreygers, "Correcting the concentration index", *Journal of Health Economics*
28(2), 2009, 504-515. Wagstaff, "The bounds of the concentration index when the
variable of interest is binary", *Health Economics* 14(4), 2005, 429-432.

Demery, *Benefit Incidence: A Practitioner's Guide*, World Bank 2000.

Fortin, Lemieux and Firpo, "Decomposition methods in economics", *Handbook of
Labor Economics* 4A, 2011, section 3, on what the unexplained component is and
is not.

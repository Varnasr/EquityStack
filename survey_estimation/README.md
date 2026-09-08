# Survey estimation

Design-based estimates from complex survey data: weighted proportions and means
with standard errors that account for stratification and clustering.

Weights are the easy half and the half everyone remembers. A national household
survey is also stratified and clustered, so a standard error computed as though
the sample were independent is too small, often by a factor of two or more, and
every confidence interval and test built on it is wrong in the direction that
flatters the finding.

`design_based_estimates.py` implements the Taylor linearisation (ultimate
cluster) variance estimator, the same one behind Stata's `svy:` prefix and R's
`survey` package. It is not tied to any particular survey.

```python
from survey_estimation import svy_prop_by
svy_prop_by(df, "stunted", by="wealth_quintile")
```

The DataFrame needs a weight, a PSU and a stratum column. Everything else is
optional.

## Two things it does that a hand-rolled version usually does not

**Subgroups are estimated as domains, not subsets.** Filtering the data before
estimating a subgroup throws away the PSUs that contain none of its members.
Those PSUs are still part of the design and still count towards the stratum's
cluster total, so dropping them understates the standard error. Pass `domain=`
or use `svy_prop_by`, and they are kept.

**Proportions get a logit interval.** Near zero or one, a linear interval runs
outside [0, 1] and reports something that is not a proportion. In the test
suite, a 2.5 percent outcome concentrated in one cluster produces a linear
lower bound of -0.024 and a logit lower bound of 0.003.

**The interval says which distribution produced it.** Degrees of freedom are
clusters minus strata, and with a few dozen clusters the t quantile is
noticeably larger than 1.96. Every result carries a `ci_dist` field. Without
`scipy` the module falls back to the normal quantile, which makes intervals
slightly too narrow, and it warns rather than doing so quietly: on a 40-cluster,
8-stratum example the lowest quintile's interval is [17.1, 32.8] under the
normal and [16.9, 33.2] under t on 32 degrees of freedom.

## Worked example

`dhs_stunting.py` reproduces India's published NFHS-5 stunting table from the
raw children's recode, by wealth quintile, with design-based intervals. It is
the second half of a chain that starts in
[InsightStack](https://github.com/Varnasr/InsightStack)'s
`data_starters/dhs-south-asia/`:

```
# in InsightStack
python load_dhs.py IAKR7EFL.DTA --vars v190 v025 hw70 b5 --anthro --out children.csv

# here
python -m survey_estimation.dhs_stunting children.csv
```

The two repositories are coupled through a CSV rather than an import, so
neither needs the other installed.

The comparison step is the point. DHS published NFHS-5 stunting at 35.5 percent
nationally, 46.1 in the poorest wealth quintile and 22.9 in the richest. A run
that does not land within a few tenths of that has a fault upstream, and the
script names the three that account for almost all of them: an unscaled weight,
a subgroup filtered before estimation, an anthropometry flag divided instead of
dropped.

## Tests

```
python -m pytest tests/test_survey_estimation.py
```

Twelve checks, each pinned to a case with a known closed-form answer rather than
to the estimator's own output: one unit per cluster must reduce to `s / sqrt(n)`,
multiplying every weight by a million must leave the standard error unchanged,
and a sample where every unit inside a cluster is identical must produce a
design effect of exactly `(N - 1) / (n - 1)`.

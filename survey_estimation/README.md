# Survey estimation

Weighted proportions and means for stratified, clustered surveys, with
standard errors that account for the design. `design_based_estimates.py`
implements the Taylor linearisation (ultimate cluster) estimator used by
Stata's `svy:` and R's `survey`.

```python
from survey_estimation import svy_prop_by
svy_prop_by(df, "stunted", by="wealth_quintile")
```

The DataFrame needs a weight, a PSU and a stratum column.

## Behaviour

Subgroups are estimated as domains. The PSUs that contain none of the
subgroup's members stay in the design, so the standard error is not
understated. Use `domain=` or `svy_prop_by`.

Proportions get a logit interval, so a small proportion never has a negative
lower bound. In the tests, a 2.5 per cent outcome in one cluster has a linear
lower bound of -0.024 and a logit lower bound of 0.003.

Intervals use t on clusters minus strata and report the distribution in
`ci_dist`. Without `scipy` the module uses the normal quantile and warns.

## Worked example

`dhs_stunting.py` reproduces India's published NFHS-5 stunting table by
wealth quintile from the raw children's recode. The input CSV comes from
InsightStack's DHS loader:

```
# in InsightStack
python load_dhs.py IAKR7EFL.DTA --vars v190 v025 hw70 b5 --anthro --out children.csv

# here
python -m survey_estimation.dhs_stunting children.csv
```

DHS published 35.5 per cent nationally, 46.1 in the poorest quintile and 22.9
in the richest. A run that does not land within a few tenths of that has a
fault upstream. The three usual ones: an unscaled weight, a subgroup filtered
before estimation, an anthropometry flag divided instead of dropped.

## Tests

```
python -m pytest tests/test_survey_estimation.py
```

Twelve checks against closed-form answers: one unit per cluster reduces to
`s / sqrt(n)`; scaling every weight by a million leaves the standard error
unchanged; identical units within each cluster give a design effect of
`(N - 1) / (n - 1)`. A regression test against R's `survey` 4.2.1 agrees to
twelve significant figures.

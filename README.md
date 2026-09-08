# EquityStack

Python for distributional analysis and design-based survey estimation in
development research. Part of [OpenStacks](https://openstacks.dev). Status:
Stable, per the family
[maintenance policy](https://github.com/Varnasr/OpenStacks-for-Change/blob/main/MAINTENANCE.md).

Site: [varnasr.github.io/EquityStack](https://varnasr.github.io/EquityStack/).

## The two main packages

**`inequality/`** measures how unequally an outcome is spread and across whom.
Gini, Theil, Atkinson, Palma, the 80/20 ratio, Lorenz and concentration
curves, the concentration index with the Erreygers and Wagstaff corrections,
Theil within/between decomposition, Blinder-Oaxaca, and benefit incidence by
level of service. All survey-weighted. 54 tests. See
[`inequality/README.md`](inequality/README.md).

**`survey_estimation/`** gives proportions and means for stratified, clustered
surveys with standard errors that account for the design, the same estimator
as Stata's `svy:` and R's `survey`. Checked against R's `survey` 4.2.1 to
twelve significant figures. A worked example reproduces the published NFHS-5
stunting table. See [`survey_estimation/README.md`](survey_estimation/README.md).

```python
from inequality import concentration_index, theil_decomposition
from survey_estimation import svy_prop_by

svy_prop_by(df, "stunted", by="wealth_quintile")
concentration_index(df.stunted, rank_by=df.wealth_index)
theil_decomposition(df.consumption, groups=df.state)
```

## Other modules

| Module | What it does |
| --- | --- |
| `cleaning/` | Column names, types, missing values, outlier flags, a cleaning log |
| `impact_evaluation/` | Difference-in-differences, propensity score matching, regression discontinuity |
| `validation/` | Input validation with Pydantic models |
| `io_helpers/` | Chunked CSV reading, Stata and SPSS import, formatted Excel export |
| `modelling/` | Multicollinearity checks (VIF) |
| `visualisation/` | Annotated bar charts, district choropleth maps |
| `social_sector/` | Composite indices with stated direction, normalisation and weights, and a rank-sensitivity check |
| `notebooks/` | Two worked analyses: gender-disaggregated outcomes, women's time use |
| `sample_data/` | Small CSVs to try the code on |

Most of these are short. `inequality/`, `survey_estimation/` and
`impact_evaluation/` hold most of the code.

## Install and test

Python 3.11. Versions in `requirements.txt` are pinned and were verified
together.

```bash
git clone https://github.com/Varnasr/EquityStack.git
cd EquityStack
pip install -r requirements.txt
PYTHONPATH=$(pwd) pytest tests/      # 101 tests
```

## The family

| Repository | What it is for | Language |
| --- | --- | --- |
| [InsightStack](https://github.com/Varnasr/InsightStack) | MEL tools, calculators, research documentation, loaders for survey microdata | Stata, Python, R, SPSS |
| [FieldStack](https://github.com/Varnasr/FieldStack) | Field operations while a survey is in the field; sampling and weighted estimation after | R |
| **EquityStack** (this repository) | Inequality measurement and design-based survey estimation | Python |

[openstacks.dev](https://openstacks.dev) is the index.
[SignalStack](https://github.com/Varnasr/SignalStack) is the companion archive
for the [Research Rundown](https://varna.substack.com) newsletter, beside the
stacks rather than one of them.
[PolicyStack](https://github.com/Varnasr/PolicyStack) is superseded by
[PolicyDhara](https://github.com/Varnasr/PolicyDhara). RootStack, BridgeStack
and ViewStack are archived.

`survey_estimation/dhs_stunting.py` reads the CSV written by InsightStack's
DHS loader. FieldStack's `survey_tools/dhs_stunting.R` does the same in R, and
the two agree on the same data.

## Citation and license

```bibtex
@software{equitystack,
  author = {Sri Raman, Varna},
  title = {EquityStack: inequality measurement and survey estimation in Python},
  url = {https://github.com/Varnasr/EquityStack}
}
```

MIT. See [LICENSE](LICENSE).

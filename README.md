# EquityStack

**Python scripts and Jupyter notebooks for development sector data workflows.**

[![Part of OpenStacks](https://img.shields.io/badge/Part%20of-OpenStacks-blue)](https://openstacks.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Stable](https://img.shields.io/badge/Status-Stable-0969da?style=flat-square)](https://github.com/Varnasr/OpenStacks-for-Change/blob/main/MAINTENANCE.md)

> Distributional analysis and survey estimation for health, gender, education and climate equity data.

> **Status: Stable.** This repository works and is correct, but it is not under active
> development. Bug reports are welcome and issues stay open; new features are unlikely,
> and replies are measured in weeks rather than days. Dependencies are pinned deliberately
> so that a clone still runs years from now. See the [maintenance policy](https://github.com/Varnasr/OpenStacks-for-Change/blob/main/MAINTENANCE.md).

---

## What This Is

EquityStack is a collection of **Python scripts, Jupyter notebooks, and sample data** for development sector analysis. It provides ready-to-use utilities for data cleaning, validation, modelling, and visualisation — with a focus on public health, gender equity, education, and climate resilience workflows.

This is the **data pipeline layer** of [OpenStacks for Change](https://openstacks.dev) — an open ecosystem of tools for public interest research and evaluation.

## The two modules to read first

Most of this repository is technique on stand-in data. Two parts are not, and
they are what the name is about.

**`inequality/`** answers *who has it*. The Gini says how unequally consumption
is spread; the concentration index says whether stunting falls on the poor, by
how much, and comparably across states whose prevalence differs. It also
decomposes: `theil_decomposition` splits national inequality exactly into a
within-state and a between-state part, and `oaxaca_blinder` splits a group gap
into endowments and returns. `benefit_incidence` asks who actually receives a
public budget, which for tertiary health and higher education is usually not the
people it was voted for.

**`survey_estimation/`** answers *how sure are we*. Weighting is the half
everyone remembers; a national household survey is also clustered, and an
interval that ignores that is too narrow, often by half, erring in the direction
that flatters the result.

Together they are the two halves of an equity finding: the gradient, and whether
it is real.

```python
from inequality import concentration_index, theil_decomposition
from survey_estimation import svy_prop_by

svy_prop_by(df, "stunted", by="wealth_quintile")          # is the gap real?
concentration_index(df.stunted, rank_by=df.wealth_index)  # how steep is it?
theil_decomposition(df.consumption, groups=df.state)      # where does it sit?
```

`inequality/README.md` has the full function-by-function guide, the four things
that are easy to get wrong, and how to bootstrap a standard error over PSUs.

## What's Inside

### Core Modules

| Module | What It Does | Status |
|--------|-------------|--------|
| `cleaning/` | Column name standardisation, dtype conversion, missing value handling, outlier flagging, cleaning log generation | Ready |
| `impact_evaluation/` | Causal inference: Difference-in-Differences, Propensity Score Matching, Regression Discontinuity Design | Ready |
| `validation/` | Input validation with Pydantic models | Ready |
| `io_helpers/` | Chunked CSV reading, Stata/SPSS import, formatted Excel export | Ready |
| `modelling/` | Multicollinearity checks (VIF) | Ready |
| `visualisation/` | Annotated bar charts, district-level choropleth maps | Ready |
| `inequality/` | **Distributional analysis**: Gini, Theil, Atkinson, Palma, Lorenz and concentration curves, the concentration index with Erreygers and Wagstaff corrections, Theil within/between decomposition, Blinder-Oaxaca, benefit incidence | Ready |
| `social_sector/` | Composite indices with explicit direction, normalisation and weighting, plus a rank-sensitivity check | Ready |
| `survey_estimation/` | Design-based proportions and means for stratified, clustered surveys, with a worked NFHS-5 example | Ready |

### Notebooks

| Notebook | What It Does |
|----------|-------------|
| `sector_gender_summary.ipynb` | Gender-disaggregated analysis with sample data |
| `sector_wee_time_use.ipynb` | Women's economic empowerment time-use analysis |

### Data and Testing

| Directory | What It Contains |
|-----------|-----------------|
| `sample_data/` | Gender sample and time-use sample datasets |
| `tests/` | 11 pytest test files covering all core modules |
| `scripts/` | Standalone export utilities |

## Getting Started

### Prerequisites

- **Python 3.8+**
- **Jupyter** (notebook or lab)

### Installation

```bash
git clone https://github.com/Varnasr/EquityStack.git
cd EquityStack
pip install -r requirements.txt
jupyter notebook
```

### Quick Start

1. Open a notebook from `notebooks/` to see a working analysis
2. Load practice data from `sample_data/`
3. Use `cleaning/` to prepare your own data
4. Apply `modelling/` and `visualisation/` for analysis and outputs
5. Export with `io_helpers/` for Excel or dashboard-ready formats

### Key Dependencies

- pandas, numpy, scipy — data manipulation and statistics
- matplotlib, seaborn — visualisation
- statsmodels — modelling
- openpyxl, xlsxwriter — Excel I/O
- pyreadstat — Stata and SPSS I/O
- pydantic — data validation
- geopandas, folium — spatial mapping
- ydata-profiling — quick EDA reports

Versions are pinned in `requirements.txt` and were resolved together and
verified on Python 3.11 with the suite green.

## How It Connects

EquityStack is one of several stacks in the [OpenStacks](https://openstacks.dev) ecosystem:

| Stack | Focus |
|-------|-------|
| [InsightStack](https://github.com/Varnasr/InsightStack) | MEL tools, calculators, documentation |
| [FieldStack](https://github.com/Varnasr/FieldStack) | R notebooks for fieldwork and evaluation |
| **EquityStack** (this repo) | Python workflows for development data |
| [SignalStack](https://github.com/Varnasr/SignalStack) | Research Rundown newsletter archive |

**Use EquityStack when** you work in Python/Jupyter. Use **FieldStack** for R-based equivalents. Use **InsightStack** for Stata tools and MEL calculators.

## Contributing

Contributions welcome — especially from data practitioners in the development sector. See [contributing guidelines](https://github.com/Varnasr/.github/blob/main/CONTRIBUTING.md).

High-impact areas:
- **EDA tools** — correlation matrices, group summaries, data profiling
- **Modelling** — logistic regression evaluation, OLS summary tables
- **Social sector** — climate risk flags, education outcomes, gender disaggregation, WEE analysis
- **Notebooks** — more worked examples with real analysis workflows
- **Visualisation** — categorical distributions, regression diagnostics, time series

## Citation

```bibtex
@software{equitystack,
  author = {Sri Raman, Varna},
  title = {EquityStack: Python Workflows for Development Data},
  url = {https://github.com/Varnasr/EquityStack}
}
```

## License

MIT — free to use, modify, and share. See [LICENSE](LICENSE).

---

Part of [OpenStacks for Change](https://openstacks.dev). Created by [Varna Sri Raman](https://on-web.link/varna).

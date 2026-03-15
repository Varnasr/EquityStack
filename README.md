# EquityStack

**Python scripts and Jupyter notebooks for development sector data workflows.**

[![Part of OpenStacks](https://img.shields.io/badge/Part%20of-OpenStacks-blue)](https://openstacks.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Plug-and-play templates for health, gender, education, and climate equity data — built for reproducibility.

---

## What This Is

EquityStack is a collection of **Python scripts, Jupyter notebooks, and sample data** for development sector analysis. It provides ready-to-use utilities for data cleaning, validation, modelling, and visualisation — with a focus on public health, gender equity, education, and climate resilience workflows.

This is the **data pipeline layer** of [OpenStacks for Change](https://openstacks.dev) — an open ecosystem of tools for public interest research and evaluation.

## What's Inside

### Core Modules

| Module | What It Does | Status |
|--------|-------------|--------|
| `cleaning/` | Column name standardisation, dtype conversion, missing value handling | Ready |
| `validation/` | Input validation with Pydantic models | Ready |
| `io_helpers/` | Chunked CSV reading, Stata/SPSS import, formatted Excel export | Ready |
| `modelling/` | Multicollinearity checks (VIF) | Ready |
| `visualisation/` | Annotated bar charts, district-level choropleth maps | Ready |
| `social_sector/` | Public health access index | Ready |

### Notebooks

| Notebook | What It Does |
|----------|-------------|
| `sector_gender_summary.ipynb` | Gender-disaggregated analysis with sample data |
| `sector_wee_time_use.ipynb` | Women's economic empowerment time-use analysis |

### Data and Testing

| Directory | What It Contains |
|-----------|-----------------|
| `sample_data/` | Gender sample and time-use sample datasets |
| `tests/` | 10 pytest test files covering all core modules |
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

- pandas, numpy — data manipulation
- matplotlib, seaborn — visualisation
- scikit-learn, statsmodels — modelling
- openpyxl, xlsxwriter — Excel I/O
- pydantic — data validation
- geopandas, folium — spatial mapping

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

Contributions welcome — especially from data practitioners in the development sector. See [CONTRIBUTING.md](CONTRIBUTING.md).

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

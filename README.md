# EquityStack

**Python scripts and Jupyter notebooks for development sector data workflows.**

[![Part of OpenStacks](https://img.shields.io/badge/Part%20of-OpenStacks-blue)](https://openstacks.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Plug-and-play templates for health, gender, education, and climate equity data — built for reproducibility.

---

## What This Is

EquityStack is a structured collection of **Python scripts, Jupyter notebooks, and sample data** for development sector analysis. It provides ready-to-use templates for data cleaning, exploratory analysis, modelling, and visualisation — with a focus on public health, gender equity, education, and climate resilience workflows.

This is the **data pipeline layer** of [OpenStacks for Change](https://openstacks.dev) — an open ecosystem of tools for public interest research and evaluation.

## What's Inside

| Directory | What It Contains |
|-----------|-----------------|
| `notebooks/` | Jupyter notebooks with guided analysis workflows |
| `scripts/` | Standalone Python scripts for common tasks |
| `cleaning/` | Data cleaning and transformation templates |
| `eda/` | Exploratory data analysis recipes |
| `modelling/` | Statistical modelling templates (regression, classification) |
| `validation/` | Data validation and quality checks |
| `visualisation/` | Chart templates and plotting utilities |
| `social_sector/` | Domain-specific workflows (health, education, gender, WEE) |
| `io_helpers/` | File I/O utilities (CSV, Excel, API connectors) |
| `sample_data/` | Practice datasets for testing workflows |
| `workflows/` | End-to-end pipeline guides |
| `tests/` | Test suite for scripts and helpers |
| `docs/` | Additional documentation and use case guides |

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

### Typical Workflow

1. Start with a notebook from `notebooks/` that matches your analysis
2. Load practice data from `sample_data/`
3. Use `cleaning/` templates to prepare your own data
4. Run `eda/` for initial exploration
5. Apply `modelling/` templates for statistical analysis
6. Generate outputs with `visualisation/`

### Key Dependencies

- pandas, numpy — data manipulation
- matplotlib, seaborn, plotly — visualisation
- scikit-learn, statsmodels — modelling
- openpyxl — Excel I/O
- jupyter — notebooks

## How It Connects

EquityStack is one of several stacks in the [OpenStacks](https://openstacks.dev) ecosystem:

| Stack | Focus | Link |
|-------|-------|------|
| [InsightStack](https://github.com/Varnasr/InsightStack) | MEL tools, calculators, documentation | Knowledge systems |
| [FieldStack](https://github.com/Varnasr/FieldStack) | R notebooks for fieldwork & evaluation | Applied data work |
| **EquityStack** (this repo) | Python workflows for development data | You are here |
| [SignalStack](https://github.com/Varnasr/SignalStack) | Research Rundown newsletter archive | Knowledge curation |

**Use EquityStack when** you work in Python/Jupyter. Use **FieldStack** for R-based equivalents. Use **InsightStack** for Stata tools and MEL calculators.

## Contributing

Contributions welcome — especially from data practitioners in the development sector. See [CONTRIBUTING.md](CONTRIBUTING.md).

Useful contributions include:
- Jupyter notebooks from your own analysis work (anonymised)
- New cleaning or validation templates
- Domain-specific workflows (health, education, climate, gender)
- Improvements to existing scripts and documentation

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

**Created by [Varna Sri Raman](https://github.com/Varnasr)** — Development Economist & Social Researcher

# Python EquityStack Repository
![Run Python Tests](https://github.com/Varnasr/EquityStack/actions/workflows/python-tests.yml/badge.svg)


Welcome! This is a growing library of reusable Python functions and templates that I use across data analysis, MEL, and research workflows — especially in the fields of public health, gender, education, climate resilience, and women's economic empowerment in India and South Asia.

This repository is designed to help analysts, researchers, and program teams working with real-world datasets — where cleaning, formatting, and meaningful summaries are just as important as modelling. Each script is modular, documented, and ready to adapt.

---

## 🧩 What’s Inside

The snippets are grouped by task and written entirely in Python using widely supported open libraries.

### 🧼 Cleaning
- Rename columns, fix data types, handle missing values
- Great for preprocessing survey or admin datasets

### 📊 EDA
- Quick profile reports
- Correlation checks
- Group summaries (e.g. gender, caste, geography)

### 📈 Modelling
- OLS, logistic regression, diagnostics
- Multicollinearity and regression output summaries

### 📊 Visualisation
- Annotated plots, residual diagnostics
- Clean graphics for reporting or dashboard use

### 📂 I/O Helpers
- Read large `.csv`, `.sav`, `.dta` files
- Export styled Excel tables (summary reports, shareable outputs)

### 🌍 Social Sector
- Education outcome comparisons
- Gender-disaggregated summaries
- WEE time-use patterns
- Public health access indices
- Flagging climate-exposed geographies

### 🧪 Validation
- Use `pydantic` to enforce clean inputs and configs
- Helpful for reproducible pipelines and safe team workflows

---

## 🚀 Designed For

- Program teams working in MEL and research roles  
- Analysts handling messy survey, NFHS/NSSO-style data  
- Researchers translating quantitative work into usable insights  

All scripts include explanatory comments. You’re welcome to adapt, reuse, or extend for your own work.

---

## 📬 Contact

- 📧 varna[DOT]sr [AT] gmail [DOT] com  
- 🌐 https://varnasr.github.io  
- 🧵 https://www.threads.net/@varnasriraman  
- 💼 https://www.linkedin.com/in/varna

---

Let me know if you use something from here or want to collaborate on more!

---

## 🚀 Launch Notebooks in Google Colab

Use the links below to open key notebooks in Google Colab — no setup required.

- [Gender Summary Report](https://colab.research.google.com/github/Varnasr/EquityStack/blob/main/notebooks/notebooks/sector_gender_summary.ipynb)  
- [WEE Time Use Analysis](https://colab.research.google.com/github/Varnasr/EquityStack/blob/main/notebooks/notebooks/sector_wee_time_use.ipynb)  
- [Logistic Regression Evaluation](https://colab.research.google.com/github/Varnasr/EquityStack/blob/main/notebooks/notebooks/model_logistic_eval.ipynb)  
- [Education Outcomes Dashboard](https://colab.research.google.com/github/Varnasr/EquityStack/blob/main/notebooks/notebooks/education_outcomes_dashboard.ipynb)  
- [Public Health Mapping](https://colab.research.google.com/github/Varnasr/EquityStack/blob/main/notebooks/notebooks/map_public_health_data.ipynb)

Each notebook is self-contained and uses simulated or sample data so you can try it instantly.

---

## 📓 Notebooks: Working Examples vs Templates

This repository includes both **functional notebooks with sample data** and **template notebooks** with instructions only.

### ✅ Ready-to-run (with sample data)
These notebooks include real logic and run out-of-the-box:
- `sector_gender_summary.ipynb` — uses `gender_sample.csv`
- `sector_wee_time_use.ipynb` — uses `time_use_sample.csv`

### 🧩 Template notebooks
The following are structured as **reusable frameworks**, with step-by-step placeholders and markdown guidance:
- `eda_basic_profile.ipynb`
- `model_logistic_eval.ipynb`
- `viz_regression_diagnostics.ipynb`
- `map_public_health_data.ipynb`
- `evaluate_sroi.ipynb`
- `education_outcomes_dashboard.ipynb`
- `survey_weighted_summary.ipynb`
- `dashboard_prototype.ipynb`

These templates help:
- Standardise exploratory and reporting workflows
- Provide onboarding tools for junior analysts
- Reduce duplication in MEL and data analysis teams

You can plug your own datasets into them without needing to rewrite the structure.

---

## 🧾 Python Scripts and Tests

This repository includes reusable `.py` scripts for cleaning, modeling, exporting, and validation. These scripts are modular and written for use in public health, education, MEL, and WEE analysis workflows.

### ✅ What’s Included
- Scripts for survey prep, formatting, regression analysis, and data exports
- Designed to work independently or as part of custom pipelines
- Compatible with tools like pandas, statsmodels, pyreadstat, and xlsxwriter

### 🧪 Automated Testing

- The `/tests/` folder includes automated `pytest` checks for all scripts
- Tests run automatically via GitHub Actions on every push or pull request to the `main` branch
- Badge above reflects the current test status

To run tests locally:

```bash
pip install -r requirements.txt
pip install pytest
pytest tests/
```

All tests use dummy data and run without requiring field inputs.

---

## 🛣️ Roadmap

We’re actively improving this repository. Here are planned features:

- Add `examples/` folder with completed outputs
- Launch GitHub Pages docs site for walkthroughs
- Design a visual banner/logo
- Improve interactivity of notebooks
- Add versioned releases and changelogs
- Write a contributor guide for open collaboration

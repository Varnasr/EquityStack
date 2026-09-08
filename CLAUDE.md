# EquityStack

Python scripts and notebooks for development sector data workflows. Part of the
[OpenStacks](https://openstacks.dev) family. Status: Stable, per the family
[maintenance policy](https://github.com/Varnasr/OpenStacks-for-Change/blob/main/MAINTENANCE.md).

## Layout

`cleaning/`, `eda/`, `modelling/`, `validation/`, `io_helpers/`,
`impact_evaluation/`, `social_sector/`, `visualisation/`, plus the two that
carry the repository: `inequality/` for distributional analysis and
`survey_estimation/` for design-based estimates from complex surveys.
Notebooks in `notebooks/`, small CSVs in `sample_data/`, tests in `tests/`.

Sizes, so nobody has to guess again: 101 tests, and `inequality/` (about 950
lines) plus `survey_estimation/` (357) plus `impact_evaluation/` (220) are most
of the substance. The rest is technique taught against stand-in data, and some
of it is a handful of lines. That is a deliberate split, not neglect, but do not
describe a five-line snippet folder as a module in any user-facing copy: an
audit on 2026-09-08 found the landing page doing exactly that.

House style is numpydoc docstrings, one module per group of related functions,
pytest with plain asserts. Match it.

## Dependencies

**Pinned exactly, on purpose.** The maintenance policy asks that a clone still
run years from now, and an unpinned set on a Stable repository nobody is
watching is a CI failure waiting for a quiet week. Every version in
`requirements.txt` was resolved together and verified on Python 3.11 with the
suite green. Raise them deliberately and together, then re-run the suite. Do not
let a resolver do it silently.

Two things a future session should know:

- `pandas-profiling` was replaced by `ydata-profiling`. The maintainers renamed
  the package at version 4 and the import path changed with it. The old one does
  not merely warn: on Python 3.11 it fails to install, because its `htmlmin`
  dependency cannot build a wheel. CI survived on 3.10 alone.
- `validation/` uses pydantic's `@validator`, which is deprecated in pydantic 2
  and removed in 3. The pin holds it at 2.13.5. Whoever raises pydantic will need
  to move those to `@field_validator` in the same change.

## Testing

`.github/workflows/python-tests.yml` runs `pytest tests/` on pull requests and
pushes to main. 25 tests.

```
pip install -r requirements.txt
PYTHONPATH=$(pwd) pytest tests/
```

## inequality

The package that makes the repository's name true. Everything in it is a
covariance between an outcome and a position in a distribution, and positions
are where the errors hide, so three things are centralised rather than
reimplemented per function.

- **Weighted fractional ranks** live in `inequality/ranks.py` and are shared by
  the Gini, the concentration index and both curves, so those three agree by
  construction. Ties take the block midpoint, which is what the World Bank's DHS
  equity work does and what makes a wealth quintile a legitimate rank variable.
- **The mean fractional rank is exactly 0.5** for any weights and any pattern of
  ties. Three derivations depend on it and a test asserts it.
- **Sign convention: negative means concentrated among the poor.** Reversing
  `outcome` and `rank_by` returns a number in the right range with the opposite
  meaning and nothing errors, which is why the signature is
  `concentration_index(outcome, rank_by=...)`.

A raw concentration index is not comparable across different prevalences, so
`erreygers_index` and `wagstaff_index` exist; they answer different normative
questions and can disagree about the direction of change over time. Pick one per
table and say which.

**Do not add an analytic standard error to these.** The convenient regression
form people quote ignores the survey design entirely. Bootstrap over PSUs within
strata; `inequality/README.md` carries the recipe.

Tests are pinned to closed-form identities, never to previous output: the Gini
against brute-force mean absolute difference on random data, curve areas against
their indices by trapezoid, `within + between == total` for both GE(0) and
GE(1), Oaxaca's components summing to the gap under all four reference choices.

## survey_estimation

The one part worth reading before touching. It implements Taylor linearisation
(ultimate cluster) for stratified, clustered samples: the estimator behind
Stata's `svy:` and R's `survey`.

Its tests are pinned to answers known in closed form rather than to the
estimator's own output — one unit per cluster must collapse to `s / sqrt(n)`
exactly, scaling every weight by a million must not move the standard error, and
perfect intra-cluster correlation must give a design effect of exactly
`(N - 1) / (n - 1)` — plus a regression test against R's `survey` 4.2.1, which
agrees to twelve significant figures on a dataset built with no random number
generator. **Do not change the estimator without re-running those.** They exist
because a variance estimator cannot be checked by eye.

Three behaviours that look like details and are not:

- Subgroups are **domains**, not subsets. Filtering before estimating discards
  the PSUs holding none of the subgroup, which understates the standard error.
- Proportions get a **logit** interval. Near zero a linear one goes negative.
- Intervals use **t on clusters minus strata** and report which distribution
  produced them in `ci_dist`. Where `scipy` is absent the normal fallback warns
  rather than silently narrowing.

## Related repositories

`survey_estimation/dhs_stunting.py` consumes the CSV written by
[InsightStack](https://github.com/Varnasr/InsightStack)'s
`data_starters/dhs-south-asia/` loader, coupled through a file rather than an
import. [FieldStack](https://github.com/Varnasr/FieldStack)
`survey_tools/dhs_stunting.R` is the R counterpart, and the two agree to twelve
significant figures on the same data.

## Design references

The house style exists as a file: `assets/css/stack.css`, the same file in all
three stack repositories. Its tokens, type and border conventions are taken from
**openstacks.dev**, which is the one page in the family the owner considers well
designed. Use it rather than writing new CSS, and change it in one place, then
copy it to the other two.

The rules it encodes, so you do not undo them by accident: 2px borders and **no
shadows**, **no border-radius**, Bricolage Grotesque in uppercase for display,
Work Sans for prose, JetBrains Mono for labels and numbers, and colour bands
(`.band.white`, `.ash`, `.navy`, `.teal`, `.brick`, `.black`) rather than cards
floating on a page. Saffron `#f2a541` is the single accent and carries the focus
ring. No emoji anywhere.

For anything the house style does not already answer,
draw from **[kombai.com/gallery/web](https://kombai.com/gallery/web)** — the
owner's preferred reference for interface work that is genuinely well made. This
applies across all of Varna's repositories and sites, not only this one.

### Publishing traps, learned the hard way

**A folder only becomes a page if it holds a `README.md`.** GitHub Pages runs
`jekyll-readme-index`, which turns that README into the folder's index. A folder
without one returns 404. This repository has no nested-duplicate folders;
InsightStack has twelve of them (`spss_scripts/spss_scripts/`, `latex/latex/`
and so on), where the README sits one level down and the top-level path 404s
while the deeper one works. Check before assuming the trap applies here.

**Do not link-check with `python -m http.server`.** It generates directory
listings, so every folder link returns 200 locally and a third of them 404 in
production. That mistake shipped once. Build with Jekyll and check that the
built output actually contains `<dir>/index.html`.

**Source folders link to GitHub, not to the site.** Uniform, never 404s, and
honest about what they are. The designed surface is the landing page, the
calculators and the data-starter guides; everything else is code.

**`_layouts/default.html` is why a click-through still looks like the site.**
Before it existed, `_config.yml` set `theme: minima` and any rendered README
opened in a stock theme. Keep the layout, keep `defaults` applying it, and do
not reintroduce a theme.

**Descriptions are visible, not hover titles.** A `title` attribute shows on no
touch device and is announced unreliably by screen readers.

**Check the landing page on a phone, not only in the link checker.** `.row span`
in `stack.css` carries `white-space: nowrap` so the short language tag ("Python,
R") keeps to one line. Adding a description as another span inside `.row` makes
it inherit that, and the page then scrolls sideways: 1384px against a 390px
viewport, invisible on a desktop and the first thing a phone shows. The nowrap is
now scoped to `.row .t span`. After any change to a landing page, load it at
390x844 and compare `documentElement.scrollWidth` against `clientWidth`.

**Write for the person with the problem, not for the folder.** "Causal inference:
DiD, PSM, IV/2SLS, RDD and sensitivity analysis" is accurate and tells a reader
nothing about when to open it. Lead with the question ("Did the programme work,
and can you defend the answer?"), then name the methods so someone who already
knows what they want can still find it.

What actually has an interface, counted rather than assumed (2026-09-08, after
all three landing pages shipped):

| Repository | HTML | Published at |
|---|---|---|
| InsightStack | 9 files: a root `index.html`, six calculators in `calculators/`, a Taguette export page, and `_layouts/default.html` | https://varnasr.github.io/InsightStack/ |
| FieldStack | a root `index.html` and `_layouts/default.html` | https://varnasr.github.io/FieldStack/ |
| EquityStack | a root `index.html` and `_layouts/default.html` | https://varnasr.github.io/EquityStack/ |

All three now run GitHub Pages with `jekyll-readme-index` and **no theme**. An
older version of this table said InsightStack used `minima` and EquityStack was
unpublished; both were true once and neither is now.

The six calculators are the largest design surface in the stack family and the
obvious place to start. Beyond the stacks: SignalStack, Experiments,
openstacks.dev and the ImpactMojo properties.

One constraint that catches people: `Experiments` serves under a strict Content
Security Policy allowlisting specific CDNs, so a design pulling fonts or scripts
from anywhere else fails there silently. Read its `netlify.toml` before adding
any external asset.

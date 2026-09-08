"""Benefit incidence analysis: who actually receives public spending.

A health or education budget is spent on facilities. Whether the money reaches
the poor depends on who uses those facilities, and the answer is routinely the
opposite of the intention. Public tertiary hospitals and universities in most of
South Asia are used disproportionately by the better-off, so a rupee spent there
is regressive even though the facility is free at the point of use. Primary
health centres and government primary schools usually run the other way.

The method (Demery, *Benefit Incidence: A Practitioner's Guide*, World Bank
2000) is deliberately simple arithmetic on two inputs:

1. a household survey giving utilisation by living-standards group, and
2. a public expenditure figure, ideally net of cost recovery.

Group *j*'s benefit is its share of utilisation times the budget. That single
assumption, that the unit subsidy is the same for everyone using a given level
of service, is the method's whole weakness and it should be stated in any
write-up. It is wrong wherever quality varies systematically with who is being
served, which is most places. It biases the result toward finding spending
*more* progressive than it is, because a rural PHC and a district hospital are
counted as delivering the same rupee value.

What this module will not do is compare a benefit share against a population
share and call the difference targeting. That comparison ignores need, and need
is not flat across the distribution: the poorest quintile carries more disease
per person, so an equal share of health spending is already regressive relative
to need.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .concentration import concentration_index

__all__ = ["benefit_incidence", "benefit_incidence_by_level"]


def benefit_incidence(df: pd.DataFrame, *, utilisation: str, group: str,
                      spending: float, weights: str | None = None,
                      fees: str | None = None,
                      group_order: list | None = None) -> pd.DataFrame:
    """Allocate a budget across living-standards groups by their use of the service.

    Parameters
    ----------
    utilisation
        Column counting use: visits, enrolled children, admissions. Zero for a
        household that did not use the service, not missing, or that household
        drops out of the denominator and every share is overstated.
    group
        Living-standards group. A wealth quintile is the usual choice.
    spending
        Total public expenditure on the service, in the survey's own currency
        units. Net of cost recovery if you have that figure; if not, pass
        ``fees`` and read the net column.
    fees
        Optional column of what the household paid out of pocket. Where given,
        ``net_benefit`` subtracts it, which is the number that answers whether
        the household came out ahead.
    group_order
        Order for the output rows. Defaults to sorted order, which is right for
        numeric quintiles and wrong for strings like "poorest".

    Returns one row per group: utilisation share, benefit, benefit per person,
    and the share of the total each group receives.

    >>> import pandas as pd
    >>> d = pd.DataFrame({"visits": [3, 2, 1, 0], "q": [1, 2, 3, 4]})
    >>> benefit_incidence(d, utilisation="visits", group="q", spending=600)["benefit"].tolist()
    [300.0, 200.0, 100.0, 0.0]
    """
    for col in [utilisation, group] + ([weights] if weights else []) + ([fees] if fees else []):
        if col not in df.columns:
            raise KeyError(f"benefit_incidence: no column {col!r} in the frame")
    if spending <= 0:
        raise ValueError("benefit_incidence: spending must be positive")

    data = df.copy()
    data["_w"] = data[weights].astype(float) if weights else 1.0
    data["_u"] = pd.to_numeric(data[utilisation], errors="coerce")
    if data["_u"].isna().any():
        missing = int(data["_u"].isna().sum())
        raise ValueError(
            f"benefit_incidence: {missing} rows have missing utilisation. A household "
            "that did not use the service should be a zero, not a blank; leaving it "
            "blank drops it from the denominator and inflates every share.")
    if (data["_u"] < 0).any():
        raise ValueError("benefit_incidence: negative utilisation")

    data["_wu"] = data["_w"] * data["_u"]
    total_u = data["_wu"].sum()
    if total_u <= 0:
        raise ValueError("benefit_incidence: nobody in the sample used the service")
    total_w = data["_w"].sum()

    agg = {"_w": "sum", "_wu": "sum", utilisation: "size"}
    g = data.groupby(group, dropna=False, observed=True).agg(
        population=("_w", "sum"), utilisation=("_wu", "sum"), n=(utilisation, "size"))
    g = g.reset_index()

    g["utilisation_share"] = g["utilisation"] / total_u
    g["population_share"] = g["population"] / total_w
    g["benefit"] = g["utilisation_share"] * spending
    g["benefit_per_person"] = g["benefit"] / g["population"]

    if fees is not None:
        paid = data.assign(_f=data["_w"] * pd.to_numeric(data[fees], errors="coerce").fillna(0.0))
        f = paid.groupby(group, dropna=False, observed=True)["_f"].sum().reset_index(name="fees_paid")
        g = g.merge(f, on=group, how="left")
        g["net_benefit"] = g["benefit"] - g["fees_paid"]
        g["net_benefit_per_person"] = g["net_benefit"] / g["population"]

    if group_order is not None:
        g[group] = pd.Categorical(g[group], categories=group_order, ordered=True)
        g = g.sort_values(group)
    else:
        g = g.sort_values(group)

    # The concentration index of the benefit, computed on the household rows so
    # that within-group variation in utilisation is not thrown away by the
    # groupby. This is the one number that says progressive or regressive.
    ci = concentration_index(data["_u"], rank_by=data[group], weights=data["_w"])
    g.attrs["concentration_index"] = ci
    g.attrs["verdict"] = (
        "progressive: the benefit is concentrated among the poorer groups" if ci < -0.01
        else "regressive: the benefit is concentrated among the better-off" if ci > 0.01
        else "roughly proportional across groups")
    g.attrs["spending"] = float(spending)
    g.attrs["caveat"] = (
        "Assumes an identical unit subsidy for every user of this service. Where "
        "quality rises with the wealth of the catchment, this understates how "
        "regressive the spending is.")
    return g.reset_index(drop=True)


def benefit_incidence_by_level(df: pd.DataFrame, *, utilisation: str, group: str,
                               level: str, spending: dict, weights: str | None = None,
                               group_order: list | None = None) -> dict:
    """Benefit incidence run separately per service level, then aggregated.

    The level split is where the interesting result usually lives. Aggregate
    health spending often looks close to proportional while primary care is
    strongly progressive and tertiary care strongly regressive, the two
    cancelling in the total. Running the whole budget as one number hides
    exactly the finding a ministry can act on.

    Parameters
    ----------
    level
        Column naming the service level: primary / secondary / tertiary, or
        PHC / CHC / district hospital.
    spending
        Mapping from each level to its budget. Every level present in the data
        must appear, because a missing one is silently allocated nothing and the
        aggregate shares then do not mean what they say.

    Returns a dict with ``by_level`` (a frame per level), ``total`` (the
    aggregated frame) and ``concentration_index`` per level plus overall.
    """
    if level not in df.columns:
        raise KeyError(f"benefit_incidence_by_level: no column {level!r} in the frame")
    present = set(pd.unique(df[level].dropna()))
    missing = present - set(spending)
    if missing:
        raise ValueError(
            f"benefit_incidence_by_level: no budget given for level(s) {sorted(missing)}. "
            "A level with no entry would be allocated nothing and the aggregate shares "
            "would not sum to the budget you think they do.")

    per_level, frames, cis = {}, [], {}
    for lv, part in df.groupby(level, dropna=True, observed=True):
        out = benefit_incidence(part, utilisation=utilisation, group=group,
                                spending=spending[lv], weights=weights,
                                group_order=group_order)
        per_level[lv] = out
        cis[lv] = out.attrs["concentration_index"]
        frames.append(out[[group, "benefit", "population"]].assign(**{level: lv}))

    stacked = pd.concat(frames, ignore_index=True)
    total = stacked.groupby(group, observed=True).agg(
        benefit=("benefit", "sum"), population=("population", "max")).reset_index()
    total["benefit_share"] = total["benefit"] / total["benefit"].sum()
    total["population_share"] = total["population"] / total["population"].sum()
    total["benefit_per_person"] = total["benefit"] / total["population"]
    if group_order is not None:
        total[group] = pd.Categorical(total[group], categories=group_order, ordered=True)
        total = total.sort_values(group).reset_index(drop=True)

    overall = concentration_index(total["benefit"] / total["population"],
                                  rank_by=total[group], weights=total["population"])
    return {"by_level": per_level, "total": total,
            "concentration_index_by_level": cis,
            "concentration_index_overall": overall,
            "spending": dict(spending)}

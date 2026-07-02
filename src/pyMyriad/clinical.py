"""Clinical-trial table helpers built on pyMyriad's analysis primitives.

Main functions:
- lab_summary_table(): The canonical clinical-trial lab table — rows are
  Visit x Statistic (n / Mean (SD) / Median (Q1, Q3) / Min-Max), columns
  are treatment Arm x {Value, Change from Baseline}.

See also:
    - examples/lab_summary_table_demo.py: End-to-end usage example.
"""

from typing import TYPE_CHECKING, Optional, Union

import numpy as np
import pandas as pd

from .analysis_tree import AnalysisTree
from .listing import simple_table
from .tabular import change_from_baseline

if TYPE_CHECKING:
    from great_tables import GT

_STAT_LABELS = {
    "n": "n",
    "mean_sd": "Mean (SD)",
    "median_iqr": "Median (Q1, Q3)",
    "min_max": "Min, Max",
}


def _fmt_n(x: pd.Series) -> str:
    return str(x.notna().sum())


def _fmt_mean_sd(x: pd.Series) -> str:
    x = x.dropna()
    if len(x) == 0:
        return "NA"
    if len(x) == 1:
        return f"{x.iloc[0]:.1f} (NA)"
    return f"{np.mean(x):.1f} ({np.std(x, ddof=1):.1f})"


def _fmt_median_iqr(x: pd.Series) -> str:
    x = x.dropna()
    if len(x) == 0:
        return "NA"
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    return f"{med:.1f} ({q1:.1f}, {q3:.1f})"


def _fmt_min_max(x: pd.Series) -> str:
    x = x.dropna()
    if len(x) == 0:
        return "NA"
    return f"{np.min(x):.1f}, {np.max(x):.1f}"


_STAT_FORMATTERS = {
    "n": _fmt_n,
    "mean_sd": _fmt_mean_sd,
    "median_iqr": _fmt_median_iqr,
    "min_max": _fmt_min_max,
}


def lab_summary_table(
    df: pd.DataFrame,
    *,
    value_col: str,
    visit_col: str,
    arm_col: str,
    subject_col: str,
    baseline_level: str,
    stats: tuple[str, ...] = ("n", "mean_sd", "median_iqr", "min_max"),
    change_col: str = "_LAB_SUMMARY_CHG",
    as_gt: bool = False,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> Union[pd.DataFrame, "GT"]:
    """Build the canonical clinical-trial lab summary table.

    Produces the standard lab-value reporting layout: rows are Visit,
    sub-divided into one row per requested descriptive statistic (``n``,
    ``Mean (SD)``, ``Median (Q1, Q3)``, ``Min, Max``); columns are treatment
    Arm, each sub-divided into the observed ``Value`` and the per-subject
    paired ``Change from Baseline``.

    Internally this wraps ``change_from_baseline()`` to compute paired
    change, an ``AnalysisTree`` split by visit and arm to compute every
    (value, change) x statistic combination as a named, pre-formatted
    string statistic, ``simple_table(..., by="Arm", pivot_statistics=True)``
    to pivot Arm to columns, and a wide-to-long ``pandas`` reshape to turn
    the requested statistics into separate rows per visit — pyMyriad's
    tree/pivot machinery only pivots one axis into columns, so stacking
    statistics as rows is done here with plain pandas.

    Visit and Arm row/column ordering follows the categorical dtype order
    of ``visit_col``/``arm_col`` when present; otherwise order of first
    appearance in ``df`` is used.

    Args:
        df: Subject-level long-format DataFrame, one row per subject per
            visit (e.g. one row per USUBJID x AVISIT).
        value_col: Column with the observed lab value (e.g. ``"AVAL"``).
        visit_col: Column identifying the visit/time-point (e.g.
            ``"AVISIT"``). For guaranteed visit ordering, pass a
            ``pd.Categorical`` column with ``categories`` set in visit
            order.
        arm_col: Column identifying the treatment arm (e.g. ``"ARM"``).
            For guaranteed arm ordering, pass a ``pd.Categorical`` column.
        subject_col: Column identifying subjects (e.g. ``"USUBJID"``), used
            to pair each visit's value with that subject's baseline value.
        baseline_level: Value of ``visit_col`` that marks the baseline visit
            (e.g. ``"Baseline"``). Must be present in ``df[visit_col]``.
        stats: Which descriptive-statistic rows to include, and in what
            order. Must be a non-empty subset of ``("n", "mean_sd",
            "median_iqr", "min_max")``. Defaults to all four.
        change_col: Name of the intermediate change-from-baseline column
            computed internally via ``change_from_baseline()``. Defaults to
            a name unlikely to clash (``"_LAB_SUMMARY_CHG"``); raises if it
            already exists in ``df``.
        as_gt: If True, return a ``great_tables.GT`` object with Arm
            spanners over Value/Change sub-columns and the Visit label
            suppressed on repeated rows, instead of a plain DataFrame.
        title: Title for the GT table. Only used when ``as_gt=True``.
        subtitle: Subtitle for the GT table. Only used when ``as_gt=True``.
            Defaults to a summary of the included statistics.

    Returns:
        If ``as_gt=False`` (default): a ``pandas.DataFrame`` with columns
        ``Visit``, ``Statistic``, and one ``"{arm}||Value"`` /
        ``"{arm}||Change"`` pair of columns per arm level, one row per
        (visit, statistic) combination.

        If ``as_gt=True``: a ``great_tables.GT`` built from the same
        table, with an Arm spanner over each arm's Value/Change columns.

    Raises:
        ValueError: If ``stats`` is empty, contains a name not in
            ``("n", "mean_sd", "median_iqr", "min_max")``, or if
            ``baseline_level`` is not present in ``df[visit_col]``.
        KeyError: If ``change_col`` already exists as a column in ``df``.

    Examples:
        >>> table = lab_summary_table(
        ...     df,
        ...     value_col="AVAL",
        ...     visit_col="AVISIT",
        ...     arm_col="ARM",
        ...     subject_col="USUBJID",
        ...     baseline_level="Baseline",
        ... )
        >>> gt = lab_summary_table(
        ...     df,
        ...     value_col="AVAL",
        ...     visit_col="AVISIT",
        ...     arm_col="ARM",
        ...     subject_col="USUBJID",
        ...     baseline_level="Baseline",
        ...     stats=("n", "mean_sd"),
        ...     as_gt=True,
        ...     title="ALT (U/L) by Visit and Treatment Arm",
        ... )
    """
    if not stats:
        raise ValueError("`stats` must be a non-empty tuple.")
    unknown = set(stats) - set(_STAT_FORMATTERS)
    if unknown:
        raise ValueError(
            f"Unknown statistic name(s) {sorted(unknown)} in `stats`. "
            f"Valid options are: {sorted(_STAT_FORMATTERS)}."
        )
    if change_col in df.columns:
        raise KeyError(
            f"change_col={change_col!r} already exists as a column in `df`; "
            "pass a different change_col to avoid overwriting it."
        )
    if baseline_level not in df[visit_col].unique():
        raise ValueError(
            f"baseline_level={baseline_level!r} not found in df[{visit_col!r}]."
        )

    df = change_from_baseline(
        df,
        id_col=subject_col,
        value_col=value_col,
        baseline_level=baseline_level,
        level_col=visit_col,
        result_col=change_col,
    )

    analyze_kwargs = {}
    for stat in stats:
        fmt = _STAT_FORMATTERS[stat]
        analyze_kwargs[f"value_{stat}"] = lambda d, _fmt=fmt: _fmt(d[value_col])
        analyze_kwargs[f"change_{stat}"] = lambda d, _fmt=fmt: _fmt(d[change_col])

    tree = (
        AnalysisTree()
        .split_by(f"df.{visit_col}", label="Visit")
        .split_by(f"df.{arm_col}", label="Arm")
        .analyze_by(**analyze_kwargs, label="Lab Summary")
    )
    result = tree.run(df)

    wide = simple_table(result, by="Arm", pivot_statistics=True)
    wide = wide.drop(columns=["_Level_0"]).rename(columns={"_Level_1": "Visit"})

    arm_levels = list(pd.unique(df[arm_col]))

    blocks = []
    for stat in stats:
        block = {"Visit": wide["Visit"], "Statistic": _STAT_LABELS[stat]}
        for arm in arm_levels:
            block[f"{arm}||Value"] = wide[f"{arm}||value_{stat}"]
            block[f"{arm}||Change"] = wide[f"{arm}||change_{stat}"]
        blocks.append(pd.DataFrame(block))

    table = pd.concat(blocks, ignore_index=True)

    visit_order = {v: i for i, v in enumerate(pd.unique(wide["Visit"]))}
    stat_order = {_STAT_LABELS[s]: i for i, s in enumerate(stats)}
    table = table.sort_values(
        ["Visit", "Statistic"],
        key=lambda s: s.map(visit_order) if s.name == "Visit" else s.map(stat_order),
        kind="stable",
    ).reset_index(drop=True)

    ordered_cols = ["Visit", "Statistic"] + [
        f"{arm}||{v}" for arm in arm_levels for v in ("Value", "Change")
    ]
    table = table[ordered_cols]

    if not as_gt:
        return table

    from great_tables import GT

    display_table = table.copy()
    display_table.loc[display_table["Visit"].duplicated(), "Visit"] = ""

    arm_columns = {
        arm: [c for c in display_table.columns if c.startswith(f"{arm}||")]
        for arm in arm_levels
    }

    gt = GT(display_table)
    if title is not None or subtitle is not None:
        default_subtitle = (
            "; ".join(_STAT_LABELS[s] for s in stats)
            + " — Value and Change from Baseline"
        )
        gt = gt.tab_header(title=title, subtitle=subtitle or default_subtitle)
    for arm, cols in arm_columns.items():
        gt = gt.tab_spanner(label=str(arm), columns=cols)
    gt = gt.cols_label(
        **{c: c.split("||", 1)[1] for cols in arm_columns.values() for c in cols}
    )
    gt = gt.cols_align(
        align="center", columns=[c for cols in arm_columns.values() for c in cols]
    )
    return gt

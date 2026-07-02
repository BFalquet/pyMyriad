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
    subject_col: Optional[str] = None,
    baseline_level: Optional[str] = None,
    stats: tuple[str, ...] = ("n", "mean_sd", "median_iqr", "min_max"),
    change_col: str = "CHG",
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

    Change from baseline can either be supplied or computed: if ``df``
    already contains a ``change_col`` column it is used as-is (assumed
    pre-computed by the caller); otherwise it is computed with
    ``change_from_baseline()``, which requires ``subject_col`` and
    ``baseline_level``. The function then builds an ``AnalysisTree`` split
    by visit and arm with two ``analyze_by(label=...)`` calls — one for the
    observed value, one for the change — computing each requested statistic
    as a pre-formatted string. ``simple_table(..., by=["Arm", "Analysis"],
    pivot_statistics=False)`` then pivots both the Arm split and the
    Value/Change metric into columns in a single call, leaving the
    statistics as rows.

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
            Only required when ``change_col`` must be computed (i.e. it is
            not already a column in ``df``).
        baseline_level: Value of ``visit_col`` that marks the baseline visit
            (e.g. ``"Baseline"``). Must be present in ``df[visit_col]``.
            Only required when ``change_col`` must be computed.
        stats: Which descriptive-statistic rows to include, and in what
            order. Must be a non-empty subset of ``("n", "mean_sd",
            "median_iqr", "min_max")``. Defaults to all four.
        change_col: Name of the change-from-baseline column. If ``df``
            already has this column it is used as-is (assumed pre-computed);
            otherwise it is computed via ``change_from_baseline()`` (which
            needs ``subject_col`` and ``baseline_level``). Defaults to the
            CDISC-standard ``"CHG"``.
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
        ValueError: If ``stats`` is empty or contains a name not in
            ``("n", "mean_sd", "median_iqr", "min_max")``; if ``change_col``
            must be computed but ``subject_col`` or ``baseline_level`` is
            missing; or if ``baseline_level`` is not present in
            ``df[visit_col]``.

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
        print(
            f"lab_summary_table: using existing {change_col!r} column as the "
            "change from baseline (assumed pre-computed)."
        )
    else:
        if subject_col is None or baseline_level is None:
            raise ValueError(
                f"{change_col!r} is not a column in `df`, so it must be computed: "
                "`subject_col` and `baseline_level` are required in that case."
            )
        if baseline_level not in df[visit_col].unique():
            raise ValueError(
                f"baseline_level={baseline_level!r} not found in df[{visit_col!r}]."
            )
        print(
            f"lab_summary_table: computing change from baseline into "
            f"{change_col!r} via change_from_baseline()."
        )
        df = change_from_baseline(
            df,
            id_col=subject_col,
            value_col=value_col,
            baseline_level=baseline_level,
            level_col=visit_col,
            result_col=change_col,
        )

    # One analyze_by() per metric: same formatted statistics, computed on the
    # observed value vs. the change column. The label= tags which metric each
    # result belongs to, so by=["Arm", "Analysis"] can later pivot both the Arm
    # split and the Value/Change metric into columns in a single simple_table()
    # call, leaving the statistics as rows (pivot_statistics=False).
    def _kwargs(col):
        return {
            stat: (lambda d, _fmt=_STAT_FORMATTERS[stat], _c=col: _fmt(d[_c]))
            for stat in stats
        }

    tree = (
        AnalysisTree()
        .split_by(f"df.{visit_col}", label="Visit")
        .split_by(f"df.{arm_col}", label="Arm")
        .analyze_by(**_kwargs(value_col), label="Value")
        .analyze_by(**_kwargs(change_col), label="Change")
    )
    result = tree.run(df)

    table = simple_table(
        result,
        by=["Arm", "Analysis"],
        pivot_statistics=False,
        suppress_duplicates=False,
    )
    table = (
        table.drop(columns=["_Level_0"])
        .rename(columns={"_Level_1": "Visit"})
        .rename(columns={c: c.replace(" > ", "||") for c in table.columns})
    )
    table["Statistic"] = table["Statistic"].map(_STAT_LABELS)

    arm_levels = list(pd.unique(df[arm_col]))
    ordered_cols = ["Visit", "Statistic"] + [
        f"{arm}||{v}" for arm in arm_levels for v in ("Value", "Change")
    ]
    table = table[ordered_cols]
    table.columns.name = None

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

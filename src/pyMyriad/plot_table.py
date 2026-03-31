"""Forest plot table module.

This module provides a function for creating Great Tables (GT) tables with
inline forest plot images representing estimates and confidence intervals.

The hierarchy columns produced by simple_table() / cascade_table() become
the row identifiers, while an inline matplotlib forest plot (CI bar, estimate
dot, optional reference line) is rendered per row and embedded as a
base64-encoded PNG image.

Rows where CI columns are missing (NaN) — structural rows from cascade=True,
or analyses that produce different statistics — display a blank cell.

Main function:
- gt_forest_table(): Create a GT table with inline forest plots from a DataTree

Example:
    >>> from pyMyriad import AnalysisTree, gt_forest_table
    >>>
    >>> tree = AnalysisTree().split_by('df.Gender').analyze_by(
    ...     x=lambda df: np.mean(df.Income),
    ...     xmin=lambda df: np.mean(df.Income) - 1.96 * np.std(df.Income) / np.sqrt(len(df)),
    ...     xmax=lambda df: np.mean(df.Income) + 1.96 * np.std(df.Income) / np.sqrt(len(df)),
    ... )
    >>> result = tree.run(df)
    >>>
    >>> # Forest plot table with all statistic columns shown
    >>> gt_forest_table(result, x='x', xmin='xmin', xmax='xmax')
    >>>
    >>> # Title, no extra info columns
    >>> gt_forest_table(result, x='x', xmin='xmin', xmax='xmax',
    ...                 title='Income by Gender', info_columns=None)
    >>>
    >>> # Include all tree nodes
    >>> gt_forest_table(result, x='x', xmin='xmin', xmax='xmax', cascade=True)

See also:
    - listing.py: simple_table, cascade_table, gt_table
    - plots.py: forest_plot, distribution_plot
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from great_tables import GT

import pandas as pd

from .data_tree import DataTree
from .listing import cascade_table, simple_table

# Sentinel for the "show all non-CI stat columns" default
_UNSET = object()


def _make_forest_b64(
    ci_low,
    x_val,
    ci_high,
    x_axis_min: float,
    x_axis_max: float,
    ref_line: float,
) -> str:
    """Render one forest-plot row as a base64-encoded PNG string.

    Returns ``""`` when any of the three values is missing (NaN/None).
    Uses the non-interactive Agg backend directly to avoid altering global
    matplotlib state.
    """
    if pd.isna(ci_low) or pd.isna(x_val) or pd.isna(ci_high):
        return ""

    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(2.5, 0.4))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([float(ci_low), float(ci_high)], [0, 0], color="#aaaaaa", linewidth=1.5)
    ax.scatter([float(x_val)], [0], color="#2171b5", s=40, zorder=3)
    ax.axvline(x=ref_line, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlim(x_axis_min, x_axis_max)
    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def gt_forest_table(
    dtree: DataTree,
    x: str,
    xmin: str,
    xmax: str,
    info_columns=_UNSET,
    cascade: bool = False,
    by: str = "",
    autoscale: bool = True,
    suppress_duplicates: bool = True,
    ref_line: float = 1.0,
    title: str | None = None,
    subtitle: str | None = None,
) -> "GT":
    """Create a Great Tables table with inline forest plots from a DataTree.

    Calls simple_table() or cascade_table() with pivot_statistics=True,
    then renders one matplotlib forest plot per row (CI bar + estimate dot +
    reference line) embedded as a base64 PNG image in the table.

    Rows where the CI columns are missing (NaN) — for example structural rows
    from cascade=True, or analyses that produce different statistics — display
    a blank cell instead of a plot.

    Args:
        dtree (DataTree): The DataTree containing analysis results.
        x (str): Name of the statistic column used as the point estimate.
        xmin (str): Name of the statistic column used as the lower CI bound.
        xmax (str): Name of the statistic column used as the upper CI bound.
        info_columns: Statistic columns to display as plain text alongside the
            plot. Pass ``...`` (default) to show all non-CI columns, ``None``
            to show none, or a ``list[str]`` for an explicit selection.
        cascade (bool): If True, use cascade_table() for all tree nodes.
            Defaults to False.
        by (str): Split variable to pivot across columns, forwarded to the
            underlying table function. Defaults to "".
        autoscale (bool): If True, all forest plots share the same x-axis
            scale, enabling visual comparison across rows. Defaults to True.
        suppress_duplicates (bool): If True, suppress consecutive duplicate
            values in hierarchy columns for cleaner display. Defaults to True.
        ref_line (float): X position of the vertical reference line (e.g. 1.0
            for odds ratios, 0.0 for mean differences). Defaults to 1.0.
        title (str | None): Optional table title for GT.tab_header().
        subtitle (str | None): Optional table subtitle for GT.tab_header().

    Returns:
        GT: A Great Tables GT object ready to display or export.

    Raises:
        ValueError: If x, xmin, or xmax is not found in the table.
        ValueError: If a name in info_columns is not found in the table.

    Examples:
        >>> gt_forest_table(result, x='x', xmin='xmin', xmax='xmax')
        >>> gt_forest_table(result, x='x', xmin='xmin', xmax='xmax',
        ...                 title='OR by Gender', info_columns=None)
        >>> gt_forest_table(result, x='x', xmin='xmin', xmax='xmax',
        ...                 cascade=True, ref_line=0.0)
    """
    from great_tables import GT

    # --- 1. Build wide-format table -----------------------------------------
    table_fn = cascade_table if cascade else simple_table
    df = table_fn(
        dtree,
        by=by,
        pivot_statistics=True,
        suppress_duplicates=suppress_duplicates,
        split_path=True,
    )

    # --- 2. Identify column roles -------------------------------------------
    level_cols = [c for c in df.columns if c.startswith("_Level_")]
    ci_cols = {x, xmin, xmax}
    all_stat_cols = [c for c in df.columns if c not in level_cols]

    # --- 3. Validate CI columns ---------------------------------------------
    for col in (x, xmin, xmax):
        if col not in df.columns:
            raise ValueError(
                f"Column {col!r} not found in table. "
                f"Available columns: {all_stat_cols}"
            )

    # --- 4. Resolve info_columns --------------------------------------------
    if info_columns is _UNSET:
        resolved_info = [c for c in all_stat_cols if c not in ci_cols]
    elif info_columns is None:
        resolved_info = []
    else:
        resolved_info = list(info_columns)  # type: ignore[arg-type]
        for col in resolved_info:
            if col not in df.columns:
                raise ValueError(
                    f"info_columns: column {col!r} not found in table. "
                    f"Available columns: {all_stat_cols}"
                )

    # --- 5. Compute global x-axis range for autoscale -----------------------
    valid_range_df = df[[xmin, xmax]].dropna()
    x_axis_min_global: float = ref_line - 1.0
    x_axis_max_global: float = ref_line + 1.0
    if not valid_range_df.empty and autoscale:
        lo = float(valid_range_df[xmin].min())
        hi = float(valid_range_df[xmax].max())
        pad = (hi - lo) * 0.05 if hi > lo else 0.1
        x_axis_min_global = lo - pad
        x_axis_max_global = hi + pad
    # When autoscale=False, per-row range is computed in the loop below

    # --- 6. Generate per-row forest plot images -----------------------------
    df = df.copy()
    plot_cells = []
    for _, row in df.iterrows():
        if autoscale:
            row_min, row_max = x_axis_min_global, x_axis_max_global
        else:
            if pd.isna(row[xmin]) or pd.isna(row[xmax]):
                row_min, row_max = ref_line - 1.0, ref_line + 1.0
            else:
                lo, hi = float(row[xmin]), float(row[xmax])
                pad = (hi - lo) * 0.05 if hi > lo else 0.1
                row_min, row_max = lo - pad, hi + pad

        b64 = _make_forest_b64(row[xmin], row[x], row[xmax], row_min, row_max, ref_line)
        plot_cells.append(
            f'<img src="data:image/png;base64,{b64}" style="height:1.5em;"/>' if b64 else ""
        )
    df["_plot"] = plot_cells

    # --- 7. Build display DataFrame -----------------------------------------
    df_display = df[level_cols + resolved_info + ["_plot"]]

    # --- 8. Build GT --------------------------------------------------------
    gt = GT(df_display)

    level_label_map = {
        col: col.replace("_Level_", "Level ").strip() for col in level_cols
    }
    if level_label_map:
        gt = gt.cols_label(**level_label_map)  # type: ignore[arg-type]

    gt = gt.cols_label(_plot="Forest Plot")  # type: ignore[arg-type]
    gt = gt.fmt_markdown(columns="_plot")

    if title is not None or subtitle is not None:
        gt = gt.tab_header(title=title or "", subtitle=subtitle)

    return gt

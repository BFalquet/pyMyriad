"""Table generation module.

This module provides functions for generating formatted tables from DataTree
analysis results. Supports both simple pandas DataFrames and rich HTML tables
using great-tables.

Main functions:
- simple_table(): Create a pandas DataFrame table
- cascade_table(): Create a hierarchical table showing tree structure
- gt_table(): Create a formatted HTML table using great-tables

Example:
    >>> from pyMyriad import AnalysisTree, simple_table, gt_table
    >>>
    >>> # Build and run analysis
    >>> tree = AnalysisTree().split_by('df.Gender').analyze_by(
    ...     mean=lambda df: np.mean(df.Income),
    ...     count=lambda df: len(df)
    ... )
    >>> result = tree.run(df)
    >>>
    >>> # Basic DataFrame table
    >>> table = simple_table(result, by='df.Gender')
    >>> print(table)
    >>>
    >>> # Formatted HTML table
    >>> html_table = gt_table(result, title="Analysis Results")
    >>> html_table.save("report.html")

See also:
    - examples/03_tables_and_listings.ipynb: Comprehensive table examples
    - tabular.py: Data flattening and formatting utilities
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from great_tables import GT

import pandas as pd

from .data_tree import DataTree
from .tabular import flatten


def _clean_path_element(element: str) -> str:
    """Clean up path elements for display."""
    if element is None:
        return ""
    element = str(element)
    # Remove 'df.' prefix from expressions
    if element.startswith("df."):
        element = element[3:]
    return element


def _split_path_into_levels(
    df: pd.DataFrame, path_col: str = "path"
) -> tuple[pd.DataFrame, list]:
    """Split the path column into separate hierarchical level columns.

    Args:
            df: DataFrame with a path column containing lists
            path_col: Name of the column containing path lists

    Returns:
            Tuple of (DataFrame with additional Level_0, Level_1, Level_2, etc. columns,
                     List with the name of the new level columns)
    """
    if path_col not in df.columns:
        return (df, [])

    df = df.copy()

    # Clean paths: remove 'root' and 'analysis' markers
    def clean_path(path_list):
        if not isinstance(path_list, list):
            return []
        cleaned = []
        for elem in path_list:
            if elem not in ["root", "analysis", None]:
                cleaned.append(_clean_path_element(elem))
        return cleaned

    df["_cleaned_path"] = df[path_col].apply(clean_path)

    # Find maximum depth
    max_depth = df["_cleaned_path"].apply(len).max()
    if pd.isna(max_depth) or max_depth == 0:
        df = df.drop(columns=["_cleaned_path"])
        return (df, [])

    # Create level columns
    for i in range(int(max_depth)):
        df[f"_Level_{i}"] = df["_cleaned_path"].apply(
            lambda x: x[i] if i < len(x) else None
        )

    df = df.drop(columns=["_cleaned_path"])

    return (df, [f"_Level_{i}" for i in range(int(max_depth))])


def _suppress_duplicate_values(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Suppress duplicate consecutive values in specified columns.

    When the same value appears in consecutive rows, replace subsequent
    occurrences with empty string for cleaner display.

    Args:
            df: DataFrame to process
            columns: List of column names to apply suppression to

    Returns:
            DataFrame with duplicates suppressed
    """
    df = df.copy()

    for col in columns:
        if col not in df.columns:
            continue

        # Create a mask for where values change
        mask = df[col] != df[col].shift(1)

        # Keep only the first occurrence of each consecutive group
        df.loc[~mask, col] = ""

    return df


def _identify_pivot_levels(df: pd.DataFrame, by: str) -> list:
    """Identify which Level_* columns correspond to the pivot variable.

    Args:
            df: DataFrame with Level_* columns
            by: The split variable being pivoted by

    Returns:
            List of Level_* column names that contain the pivot values
    """
    if not by:
        return []

    # Clean the 'by' variable name
    by_clean = _clean_path_element(by)

    # Find level columns that contain the pivot variable
    level_cols = [c for c in df.columns if c.startswith("Level_")]
    pivot_level_cols = []

    for col in level_cols:
        # Check if this level contains the pivot variable name
        # The pivot variable appears as a value in the level before the actual pivot values
        if by_clean in df[col].values:
            # The next level column contains the actual pivot values
            col_idx = level_cols.index(col)
            if col_idx + 1 < len(level_cols):
                pivot_level_cols.append(level_cols[col_idx + 1])
            break

    return pivot_level_cols


def _create_table(
    dtree: DataTree,
    by: str = "",
    *,
    include_non_analysis: bool = False,
    include_label: bool = False,
    split_path: bool = True,
    suppress_duplicates: bool = True,
    pivot_statistics: bool = False,
) -> pd.DataFrame:
    """Internal function to create a pandas DataFrame table from a DataTree.

    Args:
            dtree: The DataTree to tabulate.
            by: Split variable name(s) to pivot across columns.
            include_non_analysis: If True, keep split/level rows.
            include_label: If True, include an 'Analysis' column with the analysis label.
            split_path: If True, split the path into separate hierarchical columns.
            suppress_duplicates: If True, suppress consecutive duplicate values in hierarchy columns.
            pivot_statistics: If True, pivot statistics into columns instead of rows.

    Returns:
            A formatted pandas DataFrame.
    """
    # Get flattened data with unnested statistics
    df = flatten(dtree, unnest=True, by=by)

    # Keep only analysis rows if not including non-analysis
    if not include_non_analysis:
        df = df[df["type"] == "analysis"].copy()

    if len(df) == 0:
        return pd.DataFrame({"Message": ["No analysis results to display"]})

    # Select columns
    df = df[
        [
            "path_pivot",
            "pivot_split",
            "pivot_lvl",
            "statistics",
            "values",
            "label",
            "depth",
        ]
    ].copy()

    # join all elements of path_pivot into a single string for display
    df["path_pivot"] = df["path_pivot"].apply(
        lambda x: (
            " > ".join([_clean_path_element(str(v)) for v in x if v is not None])
            if isinstance(x, list)
            else ""
        )
    )
    df["pivot_lvl"] = df["pivot_lvl"].apply(
        lambda x: (
            " > ".join([_clean_path_element(str(v)) for v in x if v is not None])
            if isinstance(x, list)
            else ""
        )
    )

    # Handle pivot columns if present
    pivot_columns = []

    if by != "" and pivot_statistics:
        # Pivot by both split variable and statistics
        # Use MultiIndex pivot to create hierarchical columns
        df = df.pivot_table(
            index=["depth", "path_pivot", "label"],
            columns=["pivot_lvl", "statistics"],
            values="values",
            aggfunc="first",
        ).reset_index()

        # Flatten the MultiIndex columns
        # After reset_index, ALL columns become tuples: ('name', '') for index cols, ('group', 'stat') for data cols
        new_cols = []
        for col in df.columns:
            if isinstance(col, tuple):
                if col[1] == "":
                    # This is an index column: ('depth', ''), ('path_pivot', ''), etc.
                    new_cols.append(col[0])
                else:
                    # This is a data column: ('F', 'm'), ('M', 'n'), etc.
                    new_cols.append(f"{col[0]}||{col[1]}")  # Use || as separator
            else:
                # Fallback for non-tuple columns (shouldn't happen with MultiIndex)
                new_cols.append(col)
        df.columns = new_cols

        # Get the pivot columns for later use
        pivot_columns = [col for col in df.columns if "||" in str(col)]

    elif by != "":
        # Pivot only by split variable
        pivot_columns = df["pivot_lvl"].unique().tolist()
        df = df.pivot_table(
            index=["depth", "path_pivot", "label", "statistics"],
            columns="pivot_lvl",
            values="values",
            aggfunc="first",
        ).reset_index()

    elif pivot_statistics:
        # Pivot only by statistics
        pivot_columns = df["statistics"].unique().tolist()
        df = df.pivot_table(
            index=["depth", "path_pivot", "label"],
            columns="statistics",
            values="values",
            aggfunc="first",
        ).reset_index()
    else:
        # No pivoting
        pivot_columns = ["values"]

    # Revert joining of path_pivot back to list
    df["path_pivot"] = df["path_pivot"].apply(
        lambda x: x.split(" > ") if isinstance(x, str) else []
    )

    # Split path into level columns if requested
    if split_path:
        df, pivot_level_cols = _split_path_into_levels(df, path_col="path_pivot")
    else:
        pivot_level_cols = []

    df = df.drop(columns=["path_pivot"])
    # reorder columns to have levels first
    if pivot_statistics and by == "":
        # When only pivoting statistics, don't include 'statistics' column
        display_cols = list(pivot_level_cols) + pivot_columns
    elif pivot_statistics and by != "":
        # When pivoting both, don't include 'statistics' column
        display_cols = list(pivot_level_cols) + pivot_columns
    else:
        display_cols = list(pivot_level_cols) + ["statistics"] + pivot_columns

    # Include label column if requested
    if include_label and "label" in df.columns:
        # Insert label after level columns
        label_pos = len([c for c in display_cols if c.startswith("_Level_")])
        display_cols.insert(label_pos, "label")

    display_df = df[display_cols].copy()

    # Rename columns
    rename_map = {"values": "Value"}
    if not pivot_statistics or by != "":
        rename_map["statistics"] = "Statistic"
    if include_label:
        rename_map["label"] = "Analysis"
    display_df = display_df.rename(columns=rename_map)

    # Remove rows where all level columns are None
    remaining_level_cols = [c for c in display_df.columns if c.startswith("_Level_")]
    # if remaining_level_cols:
    # 	display_df = display_df.dropna(subset=remaining_level_cols, how='all')

    # Suppress duplicate values in hierarchy columns for cleaner display
    if suppress_duplicates and remaining_level_cols:
        display_df = _suppress_duplicate_values(display_df, remaining_level_cols)

        # Final cleanup of display DataFrame
    # Replace None in level columns with "--" for better visibility
    for col in remaining_level_cols:
        display_df[col] = display_df[col].replace({None: "--"})

    return display_df


def simple_table(
    dtree: DataTree,
    by: str = "",
    *,
    include_label: bool = False,
    split_path: bool = True,
    suppress_duplicates: bool = True,
    pivot_statistics: bool = False,
) -> pd.DataFrame:
    """Create a simple pandas DataFrame table from a DataTree showing only analysis results.

    This is a lightweight alternative to gt_table that doesn't require
    the great-tables package. Only analysis rows are included.

    For a table that includes all tree nodes (splits, summaries, and analyses),
    use cascade_table() instead.

    Args:
            dtree: The DataTree to tabulate.
            by: Split variable name(s) to pivot across columns.
            include_label: If True, include an 'Analysis' column with the analysis label.
            split_path: If True, split the path into separate hierarchical columns.
            suppress_duplicates: If True, suppress consecutive duplicate values in hierarchy columns.
            pivot_statistics: If True, pivot statistics into columns instead of rows.

    Returns:
            A formatted pandas DataFrame with only analysis results.

    See Also:
            cascade_table: Similar function that includes all tree nodes.
    """
    return _create_table(
        dtree,
        by=by,
        include_non_analysis=False,
        include_label=include_label,
        split_path=split_path,
        suppress_duplicates=suppress_duplicates,
        pivot_statistics=pivot_statistics,
    )


def cascade_table(
    dtree: DataTree,
    by: str = "",
    *,
    include_label: bool = False,
    split_path: bool = True,
    suppress_duplicates: bool = True,
    pivot_statistics: bool = False,
) -> pd.DataFrame:
    """Create a pandas DataFrame table from a DataTree including all tree nodes.

    This function is similar to simple_table() but includes all tree nodes:
    splits, summaries, and analyses. This provides a complete view of the
    hierarchical analysis structure.

    When `by` is specified, analysis rows are pivoted across columns while
    non-analysis rows (splits, levels) are shown as single rows that indicate
    the tree structure.

    Args:
            dtree: The DataTree to tabulate.
            by: Split variable name(s) to pivot across columns.
            include_label: If True, include an 'Analysis' column with the analysis label.
            split_path: If True, split the path into separate hierarchical columns.
            suppress_duplicates: If True, suppress consecutive duplicate values in hierarchy columns.
            pivot_statistics: If True, pivot statistics into columns instead of rows.

    Returns:
            A formatted pandas DataFrame with all tree nodes.

    See Also:
            simple_table: Similar function that shows only analysis results.
    """
    # When by is specified, we need special handling for non-analysis rows
    if by != "":
        return _create_cascade_table_with_pivot(
            dtree,
            by=by,
            include_label=include_label,
            split_path=split_path,
            suppress_duplicates=suppress_duplicates,
            pivot_statistics=pivot_statistics,
        )

    # Without pivoting, use the standard _create_table
    return _create_table(
        dtree,
        by=by,
        include_non_analysis=True,
        include_label=include_label,
        split_path=split_path,
        suppress_duplicates=suppress_duplicates,
        pivot_statistics=pivot_statistics,
    )


def _create_cascade_table_with_pivot(
    dtree: DataTree,
    by: str,
    *,
    include_label: bool = False,
    split_path: bool = True,
    suppress_duplicates: bool = True,
    pivot_statistics: bool = False,
) -> pd.DataFrame:
    """Create a cascade table with proper handling of non-analysis rows during pivoting.

    Non-analysis rows (splits, levels) are kept as single rows showing the hierarchy,
    while analysis rows are pivoted across the specified variable.
    """
    # Get flattened data
    df = flatten(dtree, unnest=True, by=by)

    if len(df) == 0:
        return pd.DataFrame({"Message": ["No results to display"]})

    # Separate analysis and non-analysis rows
    analysis_df = df[df["type"] == "analysis"].copy()
    non_analysis_df = df[df["type"] != "analysis"].copy()

    # Get pivot levels from analysis rows to determine column structure
    pivot_levels = (
        analysis_df["pivot_lvl"]
        .apply(
            lambda x: (
                " > ".join([_clean_path_element(str(v)) for v in x if v is not None])
                if isinstance(x, list)
                else ""
            )
        )
        .unique()
        .tolist()
    )
    # Remove empty string if present
    pivot_levels = [p for p in pivot_levels if p != ""]

    # Process analysis rows with pivoting
    if len(analysis_df) > 0:
        analysis_result = _create_table(
            dtree,
            by=by,
            include_non_analysis=False,
            include_label=include_label,
            split_path=split_path,
            suppress_duplicates=False,  # We'll suppress later after merging
            pivot_statistics=pivot_statistics,
        )
    else:
        analysis_result = pd.DataFrame()

    # Process non-analysis rows - filter to keep only meaningful hierarchy rows
    if len(non_analysis_df) > 0:
        # Keep only 'level' type rows that have meaningful path info
        # Filter out 'root' and 'split' types as they don't add value in a pivoted view
        non_analysis_df = non_analysis_df[non_analysis_df["type"] == "level"].copy()

        if len(non_analysis_df) > 0:
            # Select and process non-analysis data
            non_analysis_df = non_analysis_df[
                ["path_pivot", "depth", "type", "label"]
            ].copy()

            # Convert path_pivot to string for deduplication
            non_analysis_df["path_pivot_str"] = non_analysis_df["path_pivot"].apply(
                lambda x: (
                    " > ".join(
                        [_clean_path_element(str(v)) for v in x if v is not None]
                    )
                    if isinstance(x, list)
                    else ""
                )
            )

            # Filter out rows with empty or minimal path (like just 'root')
            non_analysis_df = non_analysis_df[
                non_analysis_df["path_pivot_str"].str.len() > 0
            ]
            non_analysis_df = non_analysis_df[
                ~non_analysis_df["path_pivot_str"].isin(["", "root"])
            ]

            if len(non_analysis_df) > 0:
                non_analysis_df = non_analysis_df.drop_duplicates(
                    subset=["path_pivot_str", "depth", "type"]
                )

                # Convert path_pivot to list for _split_path_into_levels
                non_analysis_df["path_pivot"] = non_analysis_df["path_pivot_str"].apply(
                    lambda x: x.split(" > ") if isinstance(x, str) and x else []
                )
                non_analysis_df = non_analysis_df.drop(columns=["path_pivot_str"])

                # Split path into level columns
                if split_path:
                    non_analysis_df, level_cols = _split_path_into_levels(
                        non_analysis_df, path_col="path_pivot"
                    )
                else:
                    level_cols = []

                non_analysis_df = non_analysis_df.drop(columns=["path_pivot"])

                # Add placeholder columns for pivot values and statistics
                if pivot_statistics and pivot_levels:
                    # When pivoting both by variable and statistics, we need combined columns
                    stat_names = (
                        analysis_df["statistics"].dropna().unique().tolist()
                        if len(analysis_df) > 0
                        else []
                    )
                    for plvl in pivot_levels:
                        for stat in stat_names:
                            col_name = f"{plvl}||{stat}"
                            if col_name not in non_analysis_df.columns:
                                non_analysis_df[col_name] = None
                    # No Statistic column needed when pivot_statistics is True
                    non_analysis_df["Statistic"] = None
                elif pivot_levels:
                    # Just pivoting by variable
                    for plvl in pivot_levels:
                        if plvl not in non_analysis_df.columns:
                            non_analysis_df[plvl] = None
                    # Add Statistic column with hierarchy indicator
                    non_analysis_df["Statistic"] = "[level]"

                # Add label column placeholder if needed
                if include_label:
                    non_analysis_df["Analysis"] = non_analysis_df["label"]

                non_analysis_df = non_analysis_df.drop(
                    columns=["type", "label"], errors="ignore"
                )
            else:
                non_analysis_df = pd.DataFrame()
        else:
            non_analysis_df = pd.DataFrame()
    else:
        non_analysis_df = pd.DataFrame()

    # Merge analysis and non-analysis results
    if len(analysis_result) > 0 and len(non_analysis_df) > 0:
        # Get the column order from analysis result
        result_cols = list(analysis_result.columns)

        # Align non-analysis columns to match
        for col in result_cols:
            if col not in non_analysis_df.columns:
                non_analysis_df[col] = None

        # Keep only matching columns in correct order
        non_analysis_df = non_analysis_df[
            [c for c in result_cols if c in non_analysis_df.columns]
        ]

        # Add any missing columns
        for col in result_cols:
            if col not in non_analysis_df.columns:
                non_analysis_df[col] = None
        non_analysis_df = non_analysis_df[result_cols]

        # Combine and sort by depth to maintain hierarchy order
        # Add depth for sorting if not present
        if "depth" not in analysis_result.columns:
            # Estimate depth from level columns
            level_cols = [c for c in analysis_result.columns if c.startswith("_Level_")]
            if level_cols:
                analysis_result["_sort_depth"] = (
                    analysis_result[level_cols].notna().sum(axis=1)
                )
            else:
                analysis_result["_sort_depth"] = 0
        else:
            analysis_result["_sort_depth"] = analysis_result["depth"]

        if "depth" in non_analysis_df.columns:
            non_analysis_df["_sort_depth"] = non_analysis_df["depth"]
        else:
            level_cols = [c for c in non_analysis_df.columns if c.startswith("_Level_")]
            if level_cols:
                non_analysis_df["_sort_depth"] = (
                    non_analysis_df[level_cols].notna().sum(axis=1)
                )
            else:
                non_analysis_df["_sort_depth"] = 0

        # Create a path string for proper sorting
        level_cols = [c for c in result_cols if c.startswith("_Level_")]

        def create_sort_key(row):
            parts = []
            for col in level_cols:
                val = row.get(col, "")
                if pd.isna(val) or val == "" or val == "--":
                    break
                parts.append(str(val))
            return " > ".join(parts)

        analysis_result["_sort_path"] = analysis_result.apply(create_sort_key, axis=1)
        non_analysis_df["_sort_path"] = non_analysis_df.apply(create_sort_key, axis=1)

        # Mark row types for ordering (non-analysis first at each level)
        analysis_result["_row_type"] = 1  # Analysis rows come after
        non_analysis_df["_row_type"] = 0  # Non-analysis rows come first

        # Combine
        combined = pd.concat([analysis_result, non_analysis_df], ignore_index=True)

        # Sort by path then type (non-analysis first at each path)
        combined = combined.sort_values(
            ["_sort_path", "_sort_depth", "_row_type"]
        ).reset_index(drop=True)

        # Drop sorting columns
        combined = combined.drop(
            columns=["_sort_depth", "_sort_path", "_row_type", "depth"], errors="ignore"
        )

        display_df = combined
    elif len(analysis_result) > 0:
        display_df = analysis_result
    else:
        display_df = non_analysis_df

    # Final cleanup
    remaining_level_cols = [c for c in display_df.columns if c.startswith("_Level_")]

    # Suppress duplicate values in hierarchy columns
    if suppress_duplicates and remaining_level_cols:
        display_df = _suppress_duplicate_values(display_df, remaining_level_cols)

    # Replace None in level columns with "--"
    for col in remaining_level_cols:
        display_df[col] = display_df[col].replace({None: "--"})

    return display_df


def gt_table(
    dtree: DataTree,
    by: str = "",
    *,
    unnest=True,
    cascade: bool = False,
    split_path: bool = True,
    suppress_duplicates: bool = True,
    pivot_statistics: bool = False,
    title: Optional[str] = "Analysis Summary",
    subtitle: Optional[str] = None,
    decimals: int = 3,
) -> "GT":
    """Create a Great Tables (gt) display table from a DataTree.

    This builds on the long-form output of `flatten` and returns a nicely
    printable table using the Python Great Tables package.

    Args:
            dtree: The DataTree to tabulate.
            by: Split variable name(s) to pivot across columns. Use a string for a
                    single split or an iterable of split labels. If empty, no pivoting
                    is applied.
            unnest: If True, the statisttics are represented in separate rows; if False,
                    only the summary value is shown.
            cascade: If True, include all tree nodes (splits, summaries, and analyses);
                    otherwise only analysis rows are shown.
            split_path: If True, split the path into separate hierarchical columns.
            suppress_duplicates: If True, suppress consecutive duplicate values in hierarchy columns.
            pivot_statistics: If True, pivot statistics into columns instead of rows.
                    Compatible with the `by` argument - when both are used, creates
                    combined columns like "GroupName (statistic)".
            title: Optional table title.
            subtitle: Optional table subtitle.
            decimals: Number of decimals for numeric formatting.

    Returns:
            A great_tables.GT object ready for display/printing.

    Raises:
            ImportError: If the great-tables package is not installed.
    """

    try:
        from great_tables import GT
    except Exception as e:
        raise ImportError(
            "great-tables is required for gt_table(). Install with `pip install great-tables`."
        ) from e

    # Choose the appropriate table function based on cascade parameter
    table_func = cascade_table if cascade else simple_table
    display_df = table_func(
        dtree,
        by=by,
        split_path=split_path,
        suppress_duplicates=suppress_duplicates,
        pivot_statistics=pivot_statistics,
    )

    # Build the GT table
    tbl = GT(display_df)

    if title or subtitle:
        tbl = tbl.tab_header(title=title, subtitle=subtitle)

    remaining_level_cols = [c for c in display_df.columns if c.startswith("_Level_")]

    # Format numeric columns
    numeric_cols = []
    for col in display_df.columns:
        if col not in remaining_level_cols + ["Statistic", "Pivot"]:
            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(display_df[col]):
                numeric_cols.append(col)

    if numeric_cols:
        tbl = tbl.fmt_number(columns=numeric_cols, decimals=decimals)

    # Add spanners for hierarchical levels if we have multiple levels
    if len(remaining_level_cols) > 1:
        try:
            tbl = tbl.tab_spanner(label="Hierarchy", columns=remaining_level_cols)
        except Exception:
            pass

    # Add spanners for pivot groups when using pivot_statistics with by
    if pivot_statistics and by != "":
        try:
            # Identify columns with the pattern "GroupName||statistic"
            pivot_cols = [col for col in display_df.columns if "||" in str(col)]

            if pivot_cols:
                # Extract unique group names and organize columns
                group_dict = {}
                col_rename = {}

                for col in pivot_cols:
                    # Split on the separator
                    parts = col.split("||")
                    if len(parts) == 2:
                        group_name, stat_name = parts
                        if group_name not in group_dict:
                            group_dict[group_name] = []
                        group_dict[group_name].append(col)
                        # Rename column to just the statistic name
                        col_rename[col] = stat_name

                # Rename columns to remove group names
                tbl = tbl.cols_label(**col_rename)

                # Add a spanner for each group
                for group_name, cols in group_dict.items():
                    if len(cols) > 0:
                        tbl = tbl.tab_spanner(label=group_name, columns=cols)
        except Exception:
            pass

    # Style options
    try:
        tbl = tbl.opt_align_table_header(align="left")
        tbl = tbl.tab_options(
            table_font_size="12px",
            heading_background_color="#f8f9fa",
        )
    except Exception:
        pass

    return tbl

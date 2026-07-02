# Changelog

All notable changes to pyMyriad will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `pyMyriad.clinical` module with `lab_summary_table(df, *, value_col, visit_col, arm_col, subject_col, baseline_level, stats=("n", "mean_sd", "median_iqr", "min_max"), change_col="_LAB_SUMMARY_CHG", as_gt=False, title=None, subtitle=None)` — produces the canonical clinical-trial lab table directly from subject-level long-format data: rows are Visit, sub-divided into one row per requested descriptive statistic (n / Mean (SD) / Median (Q1, Q3) / Min-Max); columns are treatment Arm, sub-divided into observed Value and Change from Baseline (#65). Wraps `change_from_baseline()` for paired per-subject change, an `AnalysisTree` split by visit/arm, and `simple_table(..., by="Arm", pivot_statistics=True)` for the Arm pivot, followed by a wide-to-long reshape to stack statistics as rows (no `row_pivot=` primitive exists yet — see #62). Visit/Arm ordering follows the input's categorical dtype where present. Pass `as_gt=True` to get a formatted `great_tables.GT` with Arm spanners instead of a plain DataFrame.
- `change_from_baseline(df, *, id_col, value_col, baseline_level, level_col, result_col="CHG", warn_unmatched=False)` — new utility function (exported from `pyMyriad`) that computes per-subject paired change from baseline and appends the result as a new column to a copy of the DataFrame (#63). Subjects with no matching baseline row receive `NaN` in the result column; passing `warn_unmatched=True` emits a `UserWarning` with the count of unmatched subjects. Eliminates the two-line boilerplate (`baseline_lookup = df.loc[...].set_index(...)[...]` / `df["CHG"] = ...`) that every change-from-baseline table previously required. The notebook `examples/notebooks/08_row_pivot_clinical_table.ipynb` was updated to use it.
- `by="Analysis"` pivot support: passing `"Analysis"` (alone or combined with a real split label) as the `by=` argument to `simple_table()` / `gt_table()` / `cascade_table()` now pivots across the `analyze_by(label=...)` dimension, turning different analysis labels into side-by-side columns (#70). This enables the classic clinical change-from-baseline table in one natural chain — two `analyze_by()` calls (one for values, one for changes), `format_statistics()` to combine/format, and `simple_table(by=["Arm", "Analysis"])` to produce `{Arm} > {Label}` columns — with no data reshape, no second tree, and no extra library parameters. Two targeted additions to `DataNode.__flatten__` and `DataTree.__flatten__` in `data_tree.py`; `listing.py` drops `label` from the pivot index when `"Analysis"` is in `by`.
- **JSON serialization / deserialization** for `AnalysisTree`, enabling interoperability with AI agents and external systems:
  - `AnalysisTree.to_dict()` — serialize the full tree structure to a plain Python `dict`
  - `AnalysisTree.to_json(path=None, indent=2)` — serialize to a JSON string; optionally write to a file
  - `AnalysisTree.from_dict(data)` — reconstruct a tree from a `dict`
  - `AnalysisTree.from_json(source)` — reconstruct from a JSON string or file path (auto-detected)
  - Lambda functions are serialized by extracting their body expression (e.g. `lambda df: np.mean(df.Income)` → `"np.mean(df.Income)"`) via `ast` + `inspect`, enabling round-trips through JSON
  - New private helper `_callable_to_expr_str()` in `utils.py` for the lambda → string conversion
  - New private helpers `_node_to_dict()` and `_dict_to_node()` in `analysis_tree.py` for recursive node serialization/deserialization
  - New guide **docs/guides/interoperability.rst** documenting the JSON schema, lambda handling, and an end-to-end agent workflow example
- `drop_empty` parameter on `split_by()`, `split_at_by()`, and `split_at_root_by()` (and on `SplitNode` directly) to optionally discard split levels that produce an empty DataFrame. Defaults to `False` (backward-compatible). Useful when conditional splits may not be satisfied by every subset of the data.
- Categorical column support: `SplitNode.run()` now ties `observed=<drop_empty>` in `pandas.groupby` to the `drop_empty` parameter, so categorical split behavior is consistent with all other splits. With `drop_empty=False` (default) all category levels—including those with zero observations—are retained as empty DataFrames. With `drop_empty=True` only observed (non-empty) category levels are returned. Passing an explicit value for `observed` also silences the pandas ≥ 2.2 `FutureWarning` about the `observed` default changing. Both `groupby` calls in `plots.py` were updated to `observed=True` for the same reason.

### Documentation
- Added a module-level docstring to `src/pyMyriad/__init__.py` grouping the 13 public exports by purpose (construction, results, tables, plots, formatting) with one-line descriptions and a workflow example, so `help(pyMyriad)` is now useful (#47).

## [0.1.0] - 2026-03-22

### Added
- `denom` parameter on `AnalysisTree` for specifying the column(s) used to count unique observations at each tree level. When set, `_N` is a cumulative list of unique counts from the root to the current node, enabling proportion and rate computations
- Lambda dispatch by parameter name: `lambda df` (current group), `lambda _N` (denominator list), or `lambda df, _N` (both) — all automatically supported via `inspect.signature`
- String expressions now receive `_N` in their evaluation context when `denom` is set (e.g., `"_N[-1] / _N[0]"`)
- Multi-column denominator support: `denom=["PatientID", "Visit"]` counts unique row combinations via `drop_duplicates`
- Deprecation warning for the legacy `id` parameter on `AnalysisTree` (replaced by `denom`)
- Cross-analysis functionality for comparing multiple analysis results
- Hierarchical column display in listing tables - path now split into separate `Level_0`, `Level_1`, etc. columns for easier filtering and sorting
- New `simple_table()` function for lightweight DataFrame output without requiring the great-tables dependency
- New `cascade_table()` function for a hierarchical DataFrame view that includes all tree nodes (splits, summaries, and analyses), not just terminal analysis rows
- New `pivot_statistics` parameter to display statistics as columns instead of rows
- Path element cleaning - automatically removes `df.` prefixes, `root` and `analysis` markers for cleaner display
- Duplicate value suppression in hierarchy columns (controlled via `suppress_duplicates` parameter)
- Comprehensive test suite for listing functionality (`tests/test_listing.py`)
- Tutorial and example scripts demonstrating new listing features
- Documentation: LISTING_GUIDE.md and LISTING_IMPROVEMENTS.md

### Changed
- Completely rewrote `listing.py` with improved structure and helper functions
- Enhanced `gt_table()` with better formatting, spanners for hierarchical levels, and multi-level column support
- Improved pivot support with cleaner column names and better handling of combined pivots (by split variable + statistics)
- Better handling of non-terminal analysis results from both `.analyze_by()` and `.summarize_by()`

### Fixed
- Proper display of results at different tree depths
- Correct handling of None values in hierarchy columns (replaced with "--" for visibility)

## [0.1.0] - 2026-03-16

### Added
- Initial release of pyMyriad
- `AnalysisTree` class for building hierarchical analysis pipelines using builder pattern
- `DataTree` and `DataNode` classes for storing hierarchical analysis results
- `SplitDataNode` and `LvlDataNode` for representing data splits and levels
- `flatten()` function to convert DataTree to long-format DataFrame
- `tabulate()` function for creating wide-format tables with pivoting
- `gt_table()` function for creating formatted tables using great-tables package
- Support for splitting data by variables with `.split_by()`
- Support for summarizing data at intermediate levels with `.summarize_by()`
- Support for terminal analyses with `.analyze_by()`
- Format statistics functionality for creating custom formatted statistics (e.g., "mean ± SD")
- Utility functions for expression evaluation and scope management
- Comprehensive plotting capabilities in `plots.py`

### Documentation
- README.md with basic usage examples
- Example notebooks for listings, plots, and tutorials
- Example scripts for demonstration

[Unreleased]: https://github.com/BFalquet/pyMyriad/compare/main...crossanalysis
[0.1.0]: https://github.com/BFalquet/pyMyriad/releases/tag/v0.1.0

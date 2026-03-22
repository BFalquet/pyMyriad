# Changelog

All notable changes to pyMyriad will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

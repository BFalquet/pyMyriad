# Listing Improvements Summary

## Overview

This document summarizes the improvements made to the listing functionality in the `update_listing` branch.

## Key Changes

### 1. Hierarchical Column Display

**Before:**
```
Path                              | Statistic    | Value
----------------------------------|--------------|--------
Gender > F > Country > UK         | mean_income  | 77500.0
Gender > F > Country > US         | mean_income  | 70000.0
Gender > M > Country > UK         | mean_income  | 60000.0
Gender > M > Country > US         | mean_income  | 52500.0
```

**After:**
```
Level_0 | Level_1 | Level_2 | Level_3 | Statistic    | Value
--------|---------|---------|---------|--------------|--------
Gender  | F       | Country | UK      | mean_income  | 77500.0
Gender  | F       | Country | US      | mean_income  | 70000.0
Gender  | M       | Country | UK      | mean_income  | 60000.0
Gender  | M       | Country | US      | mean_income  | 52500.0
```

**Benefits:**
- Each hierarchy level is in its own column
- Easy to filter by specific levels (e.g., all "F" results)
- Better alignment and readability
- Natural grouping in spreadsheet applications
- Easier to sort and aggregate

### 2. New `simple_table()` Function

A lightweight alternative to `gt_table()` that:
- Returns a pandas DataFrame (no additional dependencies)
- Perfect for quick exploration and data export
- Fully compatible with pandas operations
- Can be easily exported to CSV, Excel, etc.

```python
from pyMyriad import simple_table

result = simple_table(dtree)
result.to_csv('analysis.csv', index=False)
```

### 3. Cleaner Path Elements

**Before:**
- `df.Gender` → displayed as-is
- `df.Age > 40` → displayed as-is
- Paths included 'root' and 'analysis' markers

**After:**
- `df.Gender` → `Gender`
- `df.Age > 40` → `Age > 40`
- 'root' and 'analysis' markers are hidden

### 4. Better Handling of Non-Terminal Analyses

The new listing properly displays results from both:
- **Terminal analyses** (`.analyze_by()`) - final results that stop further splitting
- **Intermediate summaries** (`.summarize_by()`) - summaries that allow continued splitting

**Example:**
```python
atree = AnalysisTree()\
    .split_by('df.Gender')\
    .summarize_by(gender_mean=lambda df: np.mean(df.Income))  # Intermediate
    .split_by('df.Country')\
    .analyze_by(country_mean=lambda df: np.mean(df.Income))   # Terminal
```

Both `gender_mean` and `country_mean` are properly displayed with their appropriate hierarchy levels.

### 5. Enhanced Pivot Support

**Before:**
- Pivot functionality existed but with complex column names
- Difficult to interpret pivoted results

**After:**
- Clean pivot column names
- Clear indication of pivot variable
- Side-by-side comparison made easy

```python
result = simple_table(dtree, by='df.Gender')
# Creates columns: Level_0, Level_1, ..., Pivot, F, M
```

## Files Changed

### Modified Files
1. **src/pyMyriad/listing.py** - Complete rewrite
   - Added `_clean_path_element()` helper
   - Added `_split_path_into_levels()` for hierarchical columns
   - Rewrote `gt_table()` with better formatting
   - Added new `simple_table()` function

2. **src/pyMyriad/__init__.py** - Export new function
   - Added `simple_table` to exports

3. **examples/scripts/script_test.py** - Updated example
   - Added demonstrations of new listing functionality
   - Shows both simple_table and traditional flatten

### New Files
1. **tests/test_listing.py** - Comprehensive test suite
   - 12 test functions covering all features
   - Tests for hierarchical columns, pivoting, edge cases

2. **examples/scripts/listing_tutorial.py** - Tutorial script
   - 7 detailed examples
   - Demonstrates all new features
   - Includes before/after comparisons

3. **docs/LISTING_GUIDE.md** - Complete documentation
   - Usage examples
   - API reference
   - Migration guide
   - Troubleshooting tips

## Usage Examples

### Basic Usage

```python
from pyMyriad import AnalysisTree, simple_table
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'Gender': ['M', 'M', 'F', 'F'],
    'Income': [50000, 60000, 70000, 80000]
})

atree = AnalysisTree()\
    .split_by('df.Gender')\
    .analyze_by(mean=lambda df: np.mean(df.Income))

dtree = atree.run(df)
result = simple_table(dtree)
print(result)
```

### With Pivot

```python
result = simple_table(dtree, by='df.Gender')
# Side-by-side comparison of M vs F
```

### With Great Tables

```python
from pyMyriad import gt_table

table = gt_table(
    dtree,
    title="Income Analysis",
    decimals=2
)
table.show()
```

## Migration Guide

### Old Code
```python
from pyMyriad.tabular import flatten

result = flatten(dtree, unnest=True)
# Manual path parsing needed
# Path is a list: ['root', 'df.Gender', 'F', 'analysis']
```

### New Code
```python
from pyMyriad import simple_table

result = simple_table(dtree)
# Automatic hierarchical columns
# Level_0='Gender', Level_1='F'
```

## Performance

The new implementation:
- Similar performance to the old flatten() function
- Slightly more memory efficient due to cleaner data structures
- Faster for filtering operations (thanks to separate level columns)

## Backward Compatibility

- The old `flatten()` and `tabulate()` functions still work
- `gt_table()` signature is backward compatible (new parameters are optional)
- Existing code will continue to work without changes
- New features are opt-in

## Testing

Run the test suite:
```bash
pytest tests/test_listing.py -v
```

Run the tutorial:
```bash
python examples/scripts/listing_tutorial.py
```

## Future Enhancements

Potential future improvements:
1. Add support for custom column names (instead of Level_0, Level_1, etc.)
2. Add export templates for common formats (LaTeX, Markdown, HTML)
3. Add interactive table support (with sorting/filtering in notebooks)
4. Add support for merging multiple DataTrees into a single table
5. Add statistical comparison columns (e.g., p-values, effect sizes)

## Conclusion

The enhanced listing functionality makes pyMyriad analysis results:
- **More readable** - Hierarchical columns are clearer than concatenated paths
- **More flexible** - simple_table() for quick work, gt_table() for reports
- **More powerful** - Better filtering, sorting, and pivoting capabilities
- **More professional** - Publication-ready output with minimal effort

The improvements maintain backward compatibility while providing a significantly better user experience for displaying and working with hierarchical analysis results.

# Enhanced Listing Functionality Guide

## Overview

The enhanced listing functionality in pyMyriad provides a clean, hierarchical way to display analysis results from DataTree objects. The key improvement is splitting the path into separate hierarchical columns (Level_0, Level_1, Level_2, etc.) instead of a single concatenated path string.

## Key Features

### 1. Hierarchical Column Display

Instead of showing paths as a single string like `"Gender > F > Country > UK"`, the new listing splits this into separate columns:

| Level_0 | Level_1 | Level_2 | Level_3 | Statistic | Value |
|---------|---------|---------|---------|-----------|-------|
| Gender  | F       | Country | UK      | mean      | 75000 |

**Benefits:**
- Easier to filter and sort by specific hierarchy levels
- Better alignment and readability
- Natural grouping in spreadsheet applications
- Clearer understanding of the analysis structure

### 2. Clean Path Elements

The listing automatically cleans up path elements:
- Removes `df.` prefixes from expressions
- Hides `root` and `analysis` markers
- Displays only meaningful hierarchy information

**Example:**
- Before: `df.Gender` → After: `Gender`
- Before: `df.Age > 40` → After: `Age > 40`

### 3. Two Functions for Different Needs

#### `simple_table()` - Lightweight, No Dependencies

Returns a pandas DataFrame with formatted results. Perfect for:
- Quick analysis and exploration
- Exporting to CSV or Excel
- Further data manipulation
- No additional package requirements

```python
from pyMyriad import simple_table

result = simple_table(dtree)
print(result)

# Export to CSV
result.to_csv('analysis_results.csv', index=False)
```

#### `gt_table()` - Beautiful Formatted Tables

Returns a Great Tables object with professional formatting. Perfect for:
- Reports and presentations
- HTML output
- Publication-ready tables
- Requires: `pip install great-tables`

```python
from pyMyriad import gt_table

table = gt_table(
    dtree,
    title="Income Analysis by Demographics",
    subtitle="Sample of 1000 participants",
    decimals=2
)
table.show()  # Display in notebook
table.save('report.html')  # Save as HTML
```

## Usage Examples

### Basic Hierarchical Analysis

```python
import pandas as pd
import numpy as np
from pyMyriad import AnalysisTree, simple_table

df = pd.DataFrame({
    'Gender': ['M', 'M', 'F', 'F', 'M', 'F'],
    'Country': ['US', 'UK', 'US', 'UK', 'US', 'UK'],
    'Income': [50000, 60000, 70000, 80000, 55000, 75000]
})

atree = AnalysisTree()\
    .split_by('df.Gender')\
    .split_by('df.Country')\
    .analyze_by(
        mean_income=lambda df: np.mean(df.Income),
        count=lambda df: len(df)
    )

dtree = atree.run(df)
result = simple_table(dtree)
print(result)
```

Output:
```
   Level_0 Level_1  Level_2 Level_3  Analysis    Statistic    Value
0   Gender       F  Country      UK  Analysis  mean_income  77500.0
1   Gender       F  Country      UK  Analysis        count      2.0
2   Gender       F  Country      US  Analysis  mean_income  70000.0
3   Gender       F  Country      US  Analysis        count      1.0
4   Gender       M  Country      UK  Analysis  mean_income  60000.0
5   Gender       M  Country      UK  Analysis        count      1.0
6   Gender       M  Country      US  Analysis  mean_income  52500.0
7   Gender       M  Country      US  Analysis        count      2.0
```

### Pivoted Analysis

Compare groups side-by-side by pivoting on a split variable:

```python
result_pivot = simple_table(dtree, by='df.Gender')
print(result_pivot)
```

Output:
```
Pivot Level_0 Level_1  Level_2 Level_3  Analysis    Statistic        F        M
0      Gender       F  Country      UK  Analysis  mean_income  77500.0      NaN
1      Gender       F  Country      UK  Analysis        count      2.0      NaN
2      Gender       F  Country      US  Analysis  mean_income  70000.0      NaN
3      Gender       F  Country      US  Analysis        count      1.0      NaN
4      Gender       M  Country      UK  Analysis  mean_income      NaN  60000.0
5      Gender       M  Country      UK  Analysis        count      NaN      1.0
6      Gender       M  Country      US  Analysis  mean_income      NaN  52500.0
7      Gender       M  Country      US  Analysis        count      NaN      2.0
```

### Multi-Level Analysis with Intermediate Summaries

Handle both terminal analyses and intermediate summaries:

```python
atree = AnalysisTree()\
    .split_by('df.Gender')\
    .summarize_by(
        gender_mean=lambda df: np.mean(df.Income),
        gender_count=lambda df: len(df)
    )\
    .split_by('df.Country')\
    .analyze_by(
        country_mean=lambda df: np.mean(df.Income),
        country_count=lambda df: len(df)
    )

dtree = atree.run(df)
result = simple_table(dtree)
```

This will show:
1. Summary statistics at the Gender level (Level_0, Level_1)
2. Detailed statistics at the Country level (Level_0, Level_1, Level_2, Level_3)

### Simple Analysis (No Splits)

Even without splits, the listing provides clean output:

```python
atree = AnalysisTree()\
    .analyze_by(
        mean=lambda df: np.mean(df.Income),
        median=lambda df: np.median(df.Income),
        std=lambda df: np.std(df.Income)
    )

dtree = atree.run(df)
result = simple_table(dtree)
```

## Function Parameters

### `simple_table(dtree, by="", include_non_analysis=False, split_path=True)`

**Parameters:**
- `dtree` (DataTree): The DataTree object to display
- `by` (str): Split variable name to pivot by (default: no pivot)
- `include_non_analysis` (bool): Include intermediate tree nodes (default: False)
- `split_path` (bool): Split paths into hierarchical columns (default: True)

**Returns:** pandas DataFrame

### `gt_table(dtree, by="", include_non_analysis=False, split_path=True, title=None, subtitle=None, decimals=3)`

**Parameters:**
- `dtree` (DataTree): The DataTree object to display
- `by` (str): Split variable name to pivot by (default: no pivot)
- `include_non_analysis` (bool): Include intermediate tree nodes (default: False)
- `split_path` (bool): Split paths into hierarchical columns (default: True)
- `title` (str): Table title (default: "Analysis Summary")
- `subtitle` (str): Table subtitle (default: None)
- `decimals` (int): Number of decimal places for numeric values (default: 3)

**Returns:** great_tables.GT object

**Requires:** `pip install great-tables`

## Advanced Usage

### Filtering Results

Since `simple_table()` returns a DataFrame, you can easily filter:

```python
result = simple_table(dtree)

# Filter to specific gender
female_results = result[result['Level_1'] == 'F']

# Filter to specific statistic
means_only = result[result['Statistic'] == 'mean_income']

# Filter to specific country at Level_3
uk_results = result[result['Level_3'] == 'UK']
```

### Exporting Results

```python
result = simple_table(dtree)

# Export to CSV
result.to_csv('analysis.csv', index=False)

# Export to Excel
result.to_excel('analysis.xlsx', index=False, sheet_name='Results')

# Export to LaTeX
print(result.to_latex(index=False))
```

### Customizing Great Tables Output

```python
from pyMyriad import gt_table

table = gt_table(
    dtree,
    by='df.Gender',
    title="Income Analysis by Demographics",
    subtitle="Stratified by Gender and Country",
    decimals=2
)

# Further customize with Great Tables methods
table = table\
    .tab_style(
        style=style.fill(color="lightblue"),
        locations=loc.body(columns="mean_income")
    )\
    .tab_footnote(
        footnote="Data collected in 2024",
        locations=loc.title()
    )

table.show()
```

### Including Non-Analysis Rows

To see the full tree structure including splits and levels:

```python
result = simple_table(dtree, include_non_analysis=True)
```

This shows:
- `type='root'`: The root node
- `type='split'`: Split nodes (where data is divided)
- `type='level'`: Level nodes (specific groups within a split)
- `type='analysis'`: Analysis results (the actual statistics)

### Disabling Path Splitting

If you prefer the old single-column path format:

```python
result = simple_table(dtree, split_path=False)
```

This keeps the path as a list in a single column instead of splitting into Level_* columns.

## Migration from Old Listing

### Old Code
```python
from pyMyriad.tabular import flatten

result = flatten(dtree, unnest=True)
# Path is a list: ['root', 'df.Gender', 'F', 'df.Country', 'UK', 'analysis']
```

### New Code
```python
from pyMyriad import simple_table

result = simple_table(dtree)
# Path is split into: Level_0='Gender', Level_1='F', Level_2='Country', Level_3='UK'
```

### Benefits of Migration
1. **Cleaner display**: No need to manually parse path lists
2. **Better filtering**: Filter by specific hierarchy levels
3. **Easier pivoting**: Built-in pivot support
4. **Professional output**: Use gt_table() for formatted reports

## Tips and Best Practices

1. **Use `simple_table()` for exploration**: Quick and lightweight, perfect for interactive analysis

2. **Use `gt_table()` for reports**: Professional formatting for presentations and publications

3. **Leverage hierarchical columns**: Filter and sort by specific levels for targeted analysis

4. **Pivot for comparisons**: Use the `by` parameter to create side-by-side comparisons

5. **Export early, export often**: Save results to CSV/Excel for sharing with non-Python users

6. **Combine with pandas**: The DataFrame output integrates seamlessly with pandas workflows

7. **Label your analyses**: Use the `label` parameter in `.analyze_by()` for clearer output

## Troubleshooting

### Issue: "No analysis results to display"
**Cause:** The DataTree has no analysis nodes, only splits.
**Solution:** Add `.analyze_by()` or `.summarize_by()` to your AnalysisTree.

### Issue: Too many Level_* columns
**Cause:** Deep hierarchy with many nested splits.
**Solution:** Consider simplifying your analysis tree or using `split_path=False`.

### Issue: NaN values in pivoted table
**Cause:** Normal behavior when pivoting - groups that don't exist show as NaN.
**Solution:** Use `fillna()` if you need to replace NaN with specific values.

### Issue: ImportError for gt_table
**Cause:** great-tables package not installed.
**Solution:** Run `pip install great-tables` or use `simple_table()` instead.

## See Also

- [Tutorial Script](../examples/scripts/listing_tutorial.py): Comprehensive examples
- [Test Suite](../tests/test_listing.py): Unit tests demonstrating functionality
- [Main Documentation](../README.md): Overall pyMyriad documentation

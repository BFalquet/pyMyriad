# Update Listing Branch - Quick Start

## What's New?

This branch introduces **hierarchical column display** for analysis results, making them much easier to read and work with.

## Quick Example

```python
from pyMyriad import AnalysisTree, simple_table
import pandas as pd
import numpy as np

# Your data
df = pd.DataFrame({
    'Gender': ['M', 'M', 'F', 'F'],
    'Country': ['US', 'UK', 'US', 'UK'],
    'Income': [50000, 60000, 70000, 80000]
})

# Define analysis
atree = AnalysisTree()\
    .split_by('df.Gender')\
    .split_by('df.Country')\
    .analyze_by(mean=lambda df: np.mean(df.Income))

# Run and display
dtree = atree.run(df)
result = simple_table(dtree)
print(result)
```

## Output

```
Level_0 | Level_1 | Level_2 | Level_3 | Analysis | Statistic | Value
--------|---------|---------|---------|----------|-----------|-------
Gender  | F       | Country | UK      | Analysis | mean      | 75000
Gender  | F       | Country | US      | Analysis | mean      | 70000
Gender  | M       | Country | UK      | Analysis | mean      | 60000
Gender  | M       | Country | US      | Analysis | mean      | 50000
```

## Key Features

✅ **Hierarchical Columns** - Each level gets its own column (Level_0, Level_1, etc.)  
✅ **Clean Labels** - Removes `df.` prefix and unnecessary markers  
✅ **Easy Filtering** - `result[result['Level_1'] == 'F']`  
✅ **Pivot Support** - `simple_table(dtree, by='df.Gender')`  
✅ **Pandas Output** - Works with all pandas operations  
✅ **No Dependencies** - `simple_table()` requires only pandas  

## Try It Out

### 1. Run the Tutorial
```bash
python examples/scripts/listing_tutorial.py
```

### 2. Run the Updated Example
```bash
cd examples/scripts
python -c "import sys; sys.path.insert(0, '../../src'); exec(open('script_test.py').read())"
```

### 3. Run the Tests
```bash
pytest tests/test_listing.py -v
```

## Documentation

- **[Complete Guide](docs/LISTING_GUIDE.md)** - Full documentation with examples
- **[Improvements Summary](docs/LISTING_IMPROVEMENTS.md)** - What changed and why
- **[Branch Summary](BRANCH_SUMMARY.md)** - Technical details for reviewers

## Comparison: Old vs New

### Old Way
```python
from pyMyriad.tabular import flatten

result = flatten(dtree, unnest=True)
# Path: ['root', 'df.Gender', 'F', 'df.Country', 'UK', 'analysis']
# Hard to filter, concatenated string
```

### New Way
```python
from pyMyriad import simple_table

result = simple_table(dtree)
# Level_0: Gender, Level_1: F, Level_2: Country, Level_3: UK
# Easy to filter: result[result['Level_1'] == 'F']
```

## Functions

### `simple_table(dtree, by="", include_non_analysis=False, split_path=True)`

Returns a pandas DataFrame with hierarchical columns.

**Parameters:**
- `dtree`: DataTree object
- `by`: Split variable to pivot by
- `include_non_analysis`: Show intermediate nodes
- `split_path`: Enable hierarchical columns

### `gt_table(dtree, by="", split_path=True, title=None, decimals=3)`

Returns a formatted Great Tables object (requires `great-tables` package).

**Parameters:**
- Same as `simple_table()` plus formatting options
- `title`: Table title
- `decimals`: Number of decimal places

## Common Tasks

### Filter by Level
```python
result = simple_table(dtree)
females = result[result['Level_1'] == 'F']
uk_only = result[result['Level_3'] == 'UK']
```

### Pivot for Comparison
```python
result = simple_table(dtree, by='df.Gender')
# Creates columns: F, M for side-by-side comparison
```

### Export to CSV
```python
result = simple_table(dtree)
result.to_csv('analysis.csv', index=False)
```

### Create Report
```python
from pyMyriad import gt_table

table = gt_table(dtree, title="Income Analysis", decimals=2)
table.save('report.html')
```

## Backward Compatibility

✅ All existing code continues to work  
✅ Old `flatten()` and `tabulate()` functions unchanged  
✅ New features are opt-in  

## Questions?

See the [Complete Guide](docs/LISTING_GUIDE.md) for detailed documentation and examples.

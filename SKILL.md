---
description: "Use the pyMyriade library to build hierarchical analysis trees, run stratified data analysis, and produce tables and plots from results."
applyTo: "**/*.py,**/*.ipynb"
---

# pyMyriade Data Analysis Skill

## What this skill is for
Use this skill whenever a user asks to analyze tabular data with pyMyriade, including building analysis trees, running stratified/grouped analyses, formatting results, and producing tables or plots.

---

## Setup

```python
import pandas as pd
import numpy as np
from pyMyriad import AnalysisTree

# Recommended: set environment once to avoid warnings
AnalysisTree.set_default_environ({'np': np, 'pd': pd})
```

---

## Core Concept: Two-Phase Pattern

pyMyriade separates **specification** from **execution**:

1. **Construction phase** — Build an `AnalysisTree` describing *what* to compute.
2. **Execution phase** — Call `.run(df)` on a `pd.DataFrame` to produce a `DataTree` of results.

```
AnalysisTree  →  .run(df)  →  DataTree
```

---

## Phase 1: Building an Analysis Tree

### Minimal pattern

```python
tree = AnalysisTree().split_by('df.Gender').analyze_by(
    n=lambda df: len(df),
    mean=lambda df: np.mean(df.Income)
)
```

### Tree-building methods (all return `self` for chaining)

| Method | Purpose |
|---|---|
| `.split_by(expr, label=None, **kwargs)` | Stratify at all current leaf nodes |
| `.split_at_root_by(expr, label=None, **kwargs)` | Force a split at the root |
| `.split_at_by(path, expr, label=None, **kwargs)` | Split at a specific tree path |
| `.analyze_by(label="", termination=True, **kwargs)` | Add terminal analysis at leaves |
| `.summarize_by(label="", **kwargs)` | Add *non-terminal* intermediate stats (allows further splits after) |
| `.summarize_at_by(path, label="", **kwargs)` | Add intermediate stats at a specific path |
| `.analyze_at_by(path, label="", **kwargs)` | Add terminal analysis at a specific path |
| `.cross_analyze_by(ref_lvl="", label="", **kwargs)` | Compare levels against a reference |

### Expression formats (two equivalent styles)

```python
# Lambda (preferred — no environment needed)
.analyze_by(mean=lambda df: np.mean(df.Score))

# String (requires numpy/pandas in environment)
.analyze_by(mean="np.mean(df.Score)")
```

### Splitting modes

```python
# Boolean split (True/False groups)
.split_by('df.Age > 18')

# Column split (one group per unique value)
.split_by('df.Gender')

# Named custom groups (can overlap or leave rows out)
.split_by(Low='df.Score < 50', Mid='df.Score < 80', High='df.Score >= 80')
```

### Targeting specific tree locations with `path`

`path` is a list of `label` values for SplitNodes.
Use `"*"` as a wildcard to match any label at a level.

```python
tree = (AnalysisTree()
    .split_by('df.Gender', label='Gender')
    .split_by('df.Country', label='Country')
    # Add extra analysis only under Gender > Country
    .summarize_at_by(['Gender', 'Country'], subtotal=lambda df: len(df))
    # Add at the root level
    .split_at_by([], 'df.AgeGroup', label='Age')
)
```

### Cross-level comparison

Compares every level against a reference level within a split:

```python
tree = (AnalysisTree()
    .split_by('df.Treatment')
    .cross_analyze_by(
        diff=lambda df, ref_df: np.mean(df.Outcome) - np.mean(ref_df.Outcome),
        ref_lvl='Control'   # omit to compare all pairs
    )
)
```

`cross_analyze_by` receives `df` (current group) and `ref_df` (reference group).

### Counting unique entities (id)

```python
# Use id= to count unique subjects rather than rows
tree = AnalysisTree(id='SubjectID').split_by('df.Arm').analyze_by(n=lambda df: len(df))
result = tree.run(df)  # _N is count of unique SubjectIDs
```

---

## Phase 2: Running the Tree

```python
result = tree.run(df)            # DataTree
result = tree.run(df, environ={'np': np, 'pd': pd})  # explicit env
```

Returns a `DataTree` (subclass of `dict`). Inspect it:

```python
print(result)          # pretty-prints the tree structure
result._N              # total entity count
```

---

## Phase 3: Working with Results

### Flatten to a DataFrame

```python
from pyMyriad.tabular import tabulate   # or: from pyMyriad import simple_table

flat = tabulate(result, unnest=True)           # long-form
flat = tabulate(result, unnest=True, pivot='df.Gender')  # pivoted by split
```

### Table functions (all return `pd.DataFrame` or great-tables HTML object)

```python
from pyMyriad import simple_table, cascade_table, gt_table

# Flat DataFrame with analysis rows only
tbl = simple_table(result)
tbl = simple_table(result, by='df.Gender')              # pivot groups to columns
tbl = simple_table(result, pivot_statistics=True)       # pivot stats to columns
tbl = simple_table(result, by='df.Gender', pivot_statistics=True)  # both

# Includes split/level nodes (full hierarchy)
tbl = cascade_table(result, by='df.Gender')

# Publication-ready HTML table (requires great-tables)
html = gt_table(result, title="My Analysis", by='df.Gender')
```

### Format statistics

```python
from pyMyriad import format_statistics

# Apply format strings to the summary dict of every DataNode
formatted = format_statistics(result, summary="{mean:.2f} ± {std:.2f}")
```

### Plots

```python
from pyMyriad import forest_plot, distribution_plot

# Requires 'x' and 'err' statistics computed in the tree
tree = tree.analyze_by(
    x=lambda df: np.mean(df.Outcome),
    err=lambda df: 1.96 * np.std(df.Outcome) / np.sqrt(len(df))
)
forest_plot(result, x='x', x_err='err')
forest_plot(result, x='x', x_err='err', col='df.Gender', jitter=True)  # faceted

# Distribution plot (uses raw data, not summaries)
distribution_plot(result, x='Outcome', type='scatter')  # or 'box', 'violin'
```

---

## Full End-to-End Example

```python
import pandas as pd
import numpy as np
from pyMyriad import AnalysisTree, simple_table, forest_plot

AnalysisTree.set_default_environ({'np': np, 'pd': pd})

df = pd.DataFrame({
    'Gender': ['M', 'M', 'F', 'F', 'M', 'F'],
    'Country': ['US', 'UK', 'US', 'UK', 'US', 'US'],
    'Income': [50000, 60000, 70000, 80000, 55000, 75000],
})

# --- Construction ---
tree = (AnalysisTree()
    .split_by('df.Gender', label='Gender')
    .split_by('df.Country', label='Country')
    .analyze_by(
        n=lambda df: len(df),
        mean=lambda df: np.mean(df.Income),
        err=lambda df: np.std(df.Income) / np.sqrt(max(len(df), 1))
    )
)

# --- Execution ---
result = tree.run(df)
print(result)

# --- Output ---
simple_table(result, by='df.Gender', pivot_statistics=True)
forest_plot(result, x='mean', x_err='err')
```

---

## Key Files

| File | Role |
|---|---|
| `src/pyMyriad/analysis_tree.py` | `AnalysisTree`, `SplitNode`, `AnalysisNode`, `CrossAnalysisNode` |
| `src/pyMyriad/data_tree.py` | `DataTree`, `SplitDataNode`, `LvlDataNode`, `DataNode` |
| `src/pyMyriad/listing.py` | `simple_table`, `cascade_table`, `gt_table` |
| `src/pyMyriad/tabular.py` | `tabulate`/`flatten`, `format_statistics` |
| `src/pyMyriad/plots.py` | `forest_plot`, `distribution_plot` |
| `examples/notebooks/` | Working Jupyter notebooks per feature |
| `ARCHITECTURE.md` | Deep-dive architecture reference |

---

## Common Pitfalls

- **String expressions warn** if numpy/pandas aren't in the environ — use lambdas or call `AnalysisTree.set_default_environ({'np': np, 'pd': pd})` once.
- **`analyze_by` is terminal** (`termination=True`) — further `split_by()` calls won't propagate past it. Use `summarize_by()` for intermediate stats.
- **`split_at_by` path uses SplitNode *labels*, not data level values** — set `label=` on `split_by()` calls to make paths predictable.
- **`cross_analyze_by` requires a prior split** — always add at least one `split_by` first.
- **`by` in table/plot functions takes the expression string** (`'df.Gender'`, not `'Gender'`).

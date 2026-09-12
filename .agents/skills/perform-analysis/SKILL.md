---
name: perform-analysis
description: Use pyMyriad to build and run an analysis tree and produce tables or plots.
---

# Skill: Perform an Analysis with pyMyriad

Use this skill when the user wants to analyze a pandas DataFrame with pyMyriad.

## Mental model

pyMyriad separates **construction** from **execution**:

1. **Construction**: build a tree with `AnalysisTree()` and chain `.split_by()`, `.analyze_by()`, etc.
2. **Execution**: call `.run(df)` to get a `DataTree` of results.
3. **Presentation**: convert the `DataTree` to a table or plot.

See [ARCHITECTURE.md](../../../ARCHITECTURE.md) for the full overview.

## Minimal template

```python
import pandas as pd
import numpy as np
from pyMyriad import AnalysisTree, simple_table

df = pd.DataFrame({
    "Group": ["A", "A", "B", "B"],
    "Value": [10, 20, 30, 40],
})

tree = (
    AnalysisTree()
    .split_by("df.Group")
    .analyze_by(
        mean=lambda df: np.mean(df.Value),
        count=lambda df: len(df),
    )
)

result = tree.run(df)
print(simple_table(result))
```

## Common patterns

### Simple analysis (no splits)

```python
tree = AnalysisTree().analyze_by(
    mean=lambda df: np.mean(df.Value),
    count=lambda df: len(df),
)
result = tree.run(df)
```

### Stratified analysis

```python
tree = (
    AnalysisTree()
    .split_by("df.Gender")
    .split_by("df.Country")
    .analyze_by(mean=lambda df: np.mean(df.Income))
)
```

### Custom groups

```python
tree = (
    AnalysisTree()
    .split_by(
        low="df.Income < 50000",
        high="df.Income >= 50000",
        label="income_level",
    )
    .analyze_by(median=lambda df: np.median(df.Income))
)
```

### Intermediate summary (non-terminating)

```python
tree = (
    AnalysisTree()
    .split_by("df.Gender")
    .summarize_by(group_mean=lambda df: np.mean(df.Score))  # does not terminate
    .split_by("df.Country")
    .analyze_by(final_mean=lambda df: np.mean(df.Score))
)
```

### Cross-level comparison

```python
tree = (
    AnalysisTree()
    .split_by("df.Treatment")
    .cross_analyze_by(
        diff=lambda df, ref_df: np.mean(df.Outcome) - np.mean(ref_df.Outcome),
        ref_lvl="Control",
    )
)
```

## Expression style

- **Prefer lambda functions** in generated code: `lambda df: np.mean(df.Value)`.
- **String expressions** work too and are useful for config-driven analysis: `"np.mean(df.Value)"`.
- `np` and `pd` are usually auto-imported; pass `environ={"np": np, "pd": pd, ...}` explicitly if you need custom functions or want to silence import warnings.

See [ARCHITECTURE.md](../../../ARCHITECTURE.md#expression-evaluation-system) for details.

## From results to outputs

```python
from pyMyriad import simple_table, gt_table, forest_plot

# Plain DataFrame
df_result = simple_table(result, by="df.Gender")

# Formatted HTML
html = gt_table(result, title="Analysis Results")

# Plot
forest_plot(result, x="mean", x_err="std")
```

See `examples/` and [README.md](../../../README.md) for more end-to-end examples.

## When to pre-process data

Some operations need data to be prepared *before* the tree runs. For example, change-from-baseline is a per-subject calculation: merge each subject's baseline value onto every row, compute `CHG`, then analyze the `CHG` column. See `examples/lab_change_from_baseline_table.py`.

## Tips

- Keep example DataFrames tiny (2–6 rows) when demonstrating.
- Test both lambda and string expressions when writing reusable functions.
- Use `format_statistics()` to combine raw statistics into presentation strings like `"mean (sd)"`.
- Use `by="Arm"` in `simple_table()` / `gt_table()` to pivot a split variable into columns.

## See also

- [ARCHITECTURE.md](../../../ARCHITECTURE.md)
- [README.md](../../../README.md)
- [examples/](../../../examples/)

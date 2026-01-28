# format_statistics Function

## Overview

The `format_statistics` function allows you to combine multiple statistics from DataNode objects into formatted strings. This is particularly useful for creating publication-ready summary statistics like "mean ± SD" or "median [IQR]".

## Function Signature

```python
format_statistics(
    dtree: DataTree, 
    format_spec: str = None,
    format_map: dict = None,
    stat_name: str = "formatted",
    remove_original: bool = False
)
```

## Parameters

- **dtree** (`DataTree`): The DataTree to modify
- **format_spec** (`str`, optional): A global format string to apply to all DataNodes. Uses Python's string formatting syntax.
- **format_map** (`dict`, optional): A dictionary mapping node labels to format strings, allowing different formats for different nodes.
- **stat_name** (`str`, optional): The name of the new formatted statistic. Defaults to "formatted".
- **remove_original** (`bool`, optional): If True, removes the original statistics that were used in the format string, keeping only the formatted result and any unused statistics. Defaults to False.

**Note**: Either `format_spec` or `format_map` (or both) must be provided.

## How It Works

1. The function traverses the entire DataTree recursively
2. For each DataNode with statistics:
   - If the node's label is in `format_map`, that format is used
   - Otherwise, if `format_spec` is provided, the global format is used
   - The format string is applied using the node's existing statistics
3. A new statistic with name `stat_name` is added to the node's summary
4. The original statistics remain unchanged

## Examples

### Example 1: Global Formatting

Apply the same format to all nodes:

```python
from pyMyriad import DataTree, DataNode, format_statistics

dtree = DataTree(
    overall = DataNode(
        label="Overall Mean", 
        summary={"m": 45.2, "sd": 8.7, "n": 150}
    ),
    baseline = DataNode(
        label="Baseline Mean", 
        summary={"m": 42.8, "sd": 9.1, "n": 150}
    )
)

# Apply global format
format_statistics(dtree, format_spec="{m} ± {sd}", stat_name="mean_sd")

print(dtree["overall"].summary["mean_sd"])
# Output: "45.2 ± 8.7"

print(dtree["baseline"].summary["mean_sd"])
# Output: "42.8 ± 9.1"
```

### Example 2: Label-Specific Formatting

Apply different formats to different node labels:

```python
dtree = DataTree(
    mean_analysis = DataNode(
        label="Mean Analysis", 
        summary={"mean": 45.2, "sd": 8.7}
    ),
    median_analysis = DataNode(
        label="Median Analysis", 
        summary={"median": 44.5, "q1": 39.2, "q3": 51.8}
    )
)

format_statistics(
    dtree,
    format_map={
        "Mean Analysis": "{mean} (SD: {sd})",
        "Median Analysis": "{median} [IQR: {q1}-{q3}]"
    },
    stat_name="formatted_result"
)

print(dtree["mean_analysis"].summary["formatted_result"])
# Output: "45.2 (SD: 8.7)"

print(dtree["median_analysis"].summary["formatted_result"])
# Output: "44.5 [IQR: 39.2-51.8]"
```

### Example 3: Numeric Formatting

Control precision and format of numeric values:

```python
dtree = DataTree(
    a = DataNode(
        label="Mean", 
        summary={"m": 10.523456, "sd": 2.3789}
    )
)

# Round to 2 decimal places
format_statistics(dtree, format_spec="{m:.2f} +/- {sd:.2f}", stat_name="rounded")

print(dtree["a"].summary["rounded"])
# Output: "10.52 +/- 2.38"
```Removing Original Statistics

Keep only the formatted result and remove intermediate statistics:

```python
dtree = DataTree(
    a = DataNode(
        label="Mean", 
        summary={"m": 10.5, "sd": 2.3, "n": 100}
    )
)

format_statistics(
    dtree, 
    format_spec="{m} +/- {sd}", 
    stat_name="result",
    remove_original=True
)

print(dtree["a"].summary)
# Output: {"n": 100, "result": "10.5 +/- 2.3"}
# Note: 'm' and 'sd' were removed, but 'n' was preserved (not used in format)
```

### Example 5: 

### Example 4: Mixed Global and Label-Specific

Use a global format with overrides for specific labels:

```python
dtree = DataTree(
    primary 6 DataNode(
        label="Primary Endpoint", 
        summary={"m": 12.5, "sd": 2.3, "ci_lower": 11.8, "ci_upper": 13.2}
    ),
    secondary = DataNode(
        label="Secondary Endpoint", 
        summary={"m": 8.7, "sd": 1.5}
    )
)

format_statistics(
    dtree,
    format_spec="{m} ± {sd}",  # Default for all nodes
    format_map={"Primary Endpoint": "{m} (95% CI: {ci_lower}-{ci_upper})"},  # Override for primary
    stat_name="display"
)

print(dtree["primary"].summary["display"])
# Output: "12.5 (95% CI: 11.8-13.2)"

print(dtree["secondary"].summary["display"])
# Output: "8.7 ± 1.5"
```

### Example 5: Nested Trees

The function works recursively on nested tree structures:

```python
fr# Example 7: Multiple Rounds of Formatting

Apply formatting progressively to build complex summaries:

```python
# Progressive formatting - keeping intermediates
dtree = DataTree(
    endpoint = DataNode(
        label="Primary",
        summary={"mean": 45.2, "sd": 8.7, "ci_lower": 42.1, "ci_upper": 48.3, "n": 150}
    )
)

# Round 1: Create mean ± SD
format_statistics(dtree, format_spec="{mean:.1f} ± {sd:.1f}", stat_name="mean_sd")

# Round 2: Create CI range
format_statistics(dtree, format_spec="({ci_lower:.1f}, {ci_upper:.1f})", stat_name="ci_range")
by default - set `remove_original=True` to clean them up
- When `remove_original=True`, only statistics used in the format string are removed; unused statistics are preserved
- Nodes without a summary dictionary are skipped
- Python's standard string formatting is used, so all format specifications are supported (e.g., `.2f` for 2 decimal places, `>10` for right-alignment, etc.)
- Multiple rounds of formatting can be applied sequentially to build complex formatted strings

## Use Cases

- Creating publication-ready summary tables
- Generating formatted statistics for reports
- Combining multiple statistics into readable text
- Standardizing the display format across a data tree
- Progressive formatting: building complex summaries step-by-step
- Cleaning up intermediate statistics to keep only final results 'mean_sd', 'ci_range', 'full_summary']
```

### Example 8: Multiple Rounds with Cleanup

Remove intermediate results for cleaner final output:

```python
dtree = DataTree(
    endpoint = DataNode(
        label="Primary",
        summary={"mean": 45.2, "sd": 8.7, "ci_lower": 42.1, "ci_upper": 48.3, "n": 150, "p": 0.023}
    )
)

# Round 1: Create mean ± SD, remove originals
format_statistics(
    dtree, 
    format_spec="{mean:.1f} ± {sd:.1f}", 
    stat_name="mean_sd",
    remove_original=True
)

# Round 2: Create CI range, remove originals
format_statistics(
    dtree,
    format_spec="({ci_lower:.1f}, {ci_upper:.1f})",
    stat_name="ci_range",
    remove_original=True
)

# Round 3: Combine into final format, remove intermediates
format_statistics(
    dtree,
    format_spec="{mean_sd}, 95% CI: {ci_range}",
    stat_name="result",
    remove_original=True
)

print(dtree["endpoint"].summary)
# Output: {'n': 150, 'p': 0.023, 'result': '45.2 ± 8.7, 95% CI: (42.1, 48.3)'}
# Only the final result and unused statistics remain
```

##om pyMyriad import DataTree, DataNode, SplitDataNode, LvlDataNode, format_statistics

dtree = DataTree(
    by_group = SplitDataNode(
        split_var="Treatment Group",
        placebo=LvlDataNode(
            split_lvl="Placebo",
            baseline=DataNode(label="Baseline", summary={"m": 42.3, "sd": 7.5}),
            week_12=DataNode(label="Week 12", summary={"m": 43.1, "sd": 7.8})
        ),
        treatment=LvlDataNode(
            split_lvl="Treatment",
            baseline=DataNode(label="Baseline", summary={"m": 41.8, "sd": 8.2}),
            week_12=DataNode(label="Week 12", summary={"m": 38.5, "sd": 7.1})
        )
    )
)

format_statistics(dtree, format_spec="{m:.1f} ± {sd:.1f}", stat_name="mean_sd")

print(dtree["by_group"]["placebo"]["baseline"].summary["mean_sd"])
# Output: "42.3 ± 7.5"
```

## Error Handling

The function will raise errors in the following cases:

1. **ValueError**: If neither `format_spec` nor `format_map` is provided
   ```python
   format_statistics(dtree)  # Raises ValueError
   ```

2. **KeyError**: If a format string references a statistic that doesn't exist
   ```python
   dtree = DataTree(a = DataNode(label="Test", summary={"m": 10}))
   format_statistics(dtree, format_spec="{m} +/- {sd}")  # Raises KeyError (no 'sd')
   ```

## Notes

- The function modifies the DataTree **in place** and also returns it for convenience
- Original statistics are preserved - only a new formatted statistic is added
- Nodes without a summary dictionary are skipped
- Python's standard string formatting is used, so all format specifications are supported (e.g., `.2f` for 2 decimal places, `>10` for right-alignment, etc.)

## Use Cases

- Creating publication-ready summary tables
- Generating formatted statistics for reports
- Combining multiple statistics into readable text
- Standardizing the display format across a data tree

# format_statistics Function

## Overview

The `format_statistics` function allows you to combine multiple statistics from DataNode objects into formatted strings. This is particularly useful for creating publication-ready summary statistics like "mean ± SD" or "median [IQR]".

## Function Signature

```python
format_statistics(
    dtree: DataTree,
    label: str = None,
    remove_original: bool = False,
    inplace: bool = False,
    safe: bool = False,
    **kwargs
)
```

## Parameters

- **dtree** (`DataTree`): The DataTree to format
- **label** (`str`, optional): If specified, only applies formatting to DataNodes with this label. If None (default), applies formatting to all DataNodes.
- **remove_original** (`bool`, optional): If True, removes the original statistics that were used in the format strings, keeping only the formatted results and any unused statistics. Defaults to False.
- **inplace** (`bool`, optional): If True, modifies the DataTree in place. If False (default), creates and returns a modified copy, leaving the original unchanged.
- **safe** (`bool`, optional): If True, raises an error when formatting fails. If False (default), silently skips nodes where formatting fails and prints a warning message.
- **\*\*kwargs**: Keyword arguments where keys are the new statistic names and values are format strings. Example: `mean_sd="{m} +/- {sd}"`

**Note**: At least one format specification must be provided via kwargs.

## How It Works

1. The function traverses the entire DataTree recursively
2. For each DataNode with statistics:
   - Checks if the node should be formatted (based on the `label` parameter)
   - Applies each format specification provided in kwargs
   - Each kwarg creates a new statistic: the key becomes the statistic name, the value is the format string
3. By default (inplace=False), returns a modified copy and leaves the original DataTree unchanged
4. If remove_original=True, statistics used in format strings are removed after formatting

## Examples

### Example 1: Basic Formatting - Apply to All Nodes

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

# Apply format to all nodes (returns a new tree by default)
new_dtree = format_statistics(dtree, mean_sd="{m} ± {sd}")

print(new_dtree["overall"].summary["mean_sd"])
# Output: "45.2 ± 8.7"

print(new_dtree["baseline"].summary["mean_sd"])
# Output: "42.8 ± 9.1"

# Original tree is unchanged
print("mean_sd" in dtree["overall"].summary)
# Output: False
```

### Example 2: Label-Specific Formatting

Apply formatting only to nodes with a specific label:

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

# Format only nodes with label "Mean Analysis"
format_statistics(
    dtree,
    label="Mean Analysis",
    formatted_result="{mean} (SD: {sd})",
    inplace=True
)

print(dtree["mean_analysis"].summary["formatted_result"])
# Output: "45.2 (SD: 8.7)"

print("formatted_result" in dtree["median_analysis"].summary)
# Output: False (not formatted because label doesn't match)

# To format the median node, call again with different label
format_statistics(
    dtree,
    label="Median Analysis",
    formatted_result="{median} [IQR: {q1}-{q3}]",
    inplace=True
)

print(dtree["median_analysis"].summary["formatted_result"])
# Output: "44.5 [IQR: 39.2-51.8]"
```

### Example 3: Multiple Formats at Once

Create multiple formatted statistics in a single call:

```python
dtree = DataTree(
    a = DataNode(
        label="Stats", 
        summary={"m": 10.5, "sd": 2.3, "n": 100}
    )
)

format_statistics(
    dtree,
    mean_sd="{m} +/- {sd}",
    sample_size="N={n}",
    mean_only="{m:.2f}",
    inplace=True
)

print(dtree["a"].summary["mean_sd"])      # Output: "10.5 +/- 2.3"
print(dtree["a"].summary["sample_size"])   # Output: "N=100"
print(dtree["a"].summary["mean_only"])     # Output: "10.50"
```

### Example 4: Numeric Formatting

Control precision and format of numeric values:

```python
dtree = DataTree(
    a = DataNode(
        label="Mean", 
        summary={"m": 10.523456, "sd": 2.3789}
    )
)

# Round to 2 decimal places
format_statistics(dtree, rounded="{m:.2f} +/- {sd:.2f}", inplace=True)

print(dtree["a"].summary["rounded"])
# Output: "10.52 +/- 2.38"
```

### Example 5: Removing Original Statistics

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
    result="{m} +/- {sd}",
    remove_original=True,
    inplace=True
)

print(dtree["a"].summary)
# Output: {"n": 100, "result": "10.5 +/- 2.3"}
# Note: 'm' and 'sd' were removed, but 'n' was preserved (not used in format)
```

### Example 6: In-Place vs Copy

Demonstrate the difference between modifying in place and creating a copy:

```python
dtree = DataTree(
    a = DataNode(label="Test", summary={"m": 12.5, "sd": 2.3})
)

# Default behavior: creates a copy
new_dtree = format_statistics(dtree, result="{m} ± {sd}")
print("result" in dtree["a"].summary)      # False - original unchanged
print("result" in new_dtree["a"].summary)  # True - new tree has the result

# In-place modification
format_statistics(dtree, result="{m} ± {sd}", inplace=True)
print("result" in dtree["a"].summary)      # True - original modified
```

### Example 7: Nested Trees

The function works recursively on nested tree structures:

```python
from pyMyriad import DataTree, DataNode, SplitDataNode, LvlDataNode, format_statistics

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

format_statistics(dtree, mean_sd="{m:.1f} ± {sd:.1f}", inplace=True)

print(dtree["by_group"]["placebo"]["baseline"].summary["mean_sd"])
# Output: "42.3 ± 7.5"

print(dtree["by_group"]["treatment"]["week_12"].summary["mean_sd"])
# Output: "38.5 ± 7.1"
```

### Example 8: Multiple Rounds of Formatting

Apply formatting progressively to build complex summaries:

```python
dtree = DataTree(
    endpoint = DataNode(
        label="Primary",
        summary={"mean": 45.2, "sd": 8.7, "ci_lower": 42.1, "ci_upper": 48.3, "n": 150}
    )
)

# Round 1: Create mean ± SD
format_statistics(dtree, mean_sd="{mean:.1f} ± {sd:.1f}", inplace=True)

# Round 2: Create CI range
format_statistics(dtree, ci_range="({ci_lower:.1f}, {ci_upper:.1f})", inplace=True)

# Round 3: Combine both into final summary
format_statistics(dtree, full_summary="{mean_sd}, 95% CI: {ci_range}", inplace=True)

print(dtree["endpoint"].summary["full_summary"])
# Output: "45.2 ± 8.7, 95% CI: (42.1, 48.3)"

print(list(dtree["endpoint"].summary.keys()))
# Output: ['mean', 'sd', 'ci_lower', 'ci_upper', 'n', 'mean_sd', 'ci_range', 'full_summary']
# All intermediate statistics are preserved by default
```

### Example 9: Multiple Rounds with Cleanup

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
    mean_sd="{mean:.1f} ± {sd:.1f}",
    remove_original=True,
    inplace=True
)

# Round 2: Create CI range, remove originals
format_statistics(
    dtree,
    ci_range="({ci_lower:.1f}, {ci_upper:.1f})",
    remove_original=True,
    inplace=True
)

# Round 3: Combine into final format, remove intermediates
format_statistics(
    dtree,
    result="{mean_sd}, 95% CI: {ci_range}",
    remove_original=True,
    inplace=True
)

print(dtree["endpoint"].summary)
# Output: {'n': 150, 'p': 0.023, 'result': '45.2 ± 8.7, 95% CI: (42.1, 48.3)'}
# Only the final result and unused statistics remain
```

### Example 10: Safe Mode - Handling Missing Statistics

Control error behavior when statistics are missing:

```python
dtree = DataTree(
    complete = DataNode(label="Complete", summary={"m": 10.5, "sd": 2.3}),
    incomplete = DataNode(label="Incomplete", summary={"m": 8.2})
)

# Default: safe=False - skip nodes with missing stats and print warning
format_statistics(dtree, result="{m} +/- {sd}", inplace=True)
# Prints: Warning: Format string for 'result' references non-existent statistic 'sd' in node 'Incomplete'...

print("result" in dtree["complete"].summary)    # True
print("result" in dtree["incomplete"].summary)  # False - skipped due to missing 'sd'

# Alternative: safe=True - raise error on missing stats
dtree2 = DataTree(
    incomplete = DataNode(label="Incomplete", summary={"m": 8.2})
)

try:
    format_statistics(dtree2, result="{m} +/- {sd}", safe=True, inplace=True)
except KeyError as e:
    print(f"Error: {e}")
    # Output: Error: Format string for 'result' references non-existent statistic 'sd'...
```

## Error Handling

The function will raise errors in the following cases:

1. **ValueError**: If no format specifications are provided in kwargs
   ```python
   format_statistics(dtree)  # Raises ValueError: At least one format specification must be provided
   ```

2. **KeyError**: If `safe=True` and a format string references a statistic that doesn't exist
   ```python
   dtree = DataTree(a = DataNode(label="Test", summary={"m": 10}))
   format_statistics(dtree, result="{m} +/- {sd}", safe=True)  
   # Raises KeyError: Format string for 'result' references non-existent statistic 'sd'
   ```

When `safe=False` (default), the function will print a warning and skip the problematic node instead of raising an error.

## Notes

- **Default behavior**: Creates a modified copy and leaves the original DataTree unchanged (inplace=False)
- **In-place modification**: Set `inplace=True` to modify the original tree
- **Original statistics**: Preserved by default; set `remove_original=True` to clean them up
- **Selective removal**: When `remove_original=True`, only statistics used in the format strings are removed; unused statistics are preserved
- **Label filtering**: Use the `label` parameter to apply formatting only to nodes with a specific label
- **Multiple formats**: Pass multiple kwargs to create several formatted statistics in one call
- **Nodes without summary**: Automatically skipped (no error raised)
- **Format specifications**: Supports all Python string formatting options (e.g., `.2f` for 2 decimal places, `>10` for right-alignment, etc.)
- **Error handling**: Use `safe=True` for strict error checking, or `safe=False` (default) to skip problematic nodes with warnings

## Use Cases

- Creating publication-ready summary tables
- Generating formatted statistics for reports
- Combining multiple statistics into readable text
- Standardizing the display format across a data tree
- Progressive formatting: building complex summaries step-by-step
- Cleaning up intermediate statistics to keep only final results
- Selective formatting: applying different formats to different node labels
- Safe data processing: using copies to preserve original data (default behavior)

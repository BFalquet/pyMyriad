"""
Example demonstrating multiple rounds of formatting with format_statistics.

This script shows how to apply formatting in multiple steps, building up
complex formatted statistics progressively.
"""

from pyMyriad import DataTree, DataNode, SplitDataNode, LvlDataNode, format_statistics

print("=" * 70)
print("Multiple Rounds of Formatting - Examples")
print("=" * 70)

# Example 1: Progressive formatting - keeping intermediates
print("\n" + "=" * 70)
print("Example 1: Progressive Formatting (Keep Intermediate Results)")
print("=" * 70)

dtree1 = DataTree(
    endpoint1 = DataNode(
        label="Primary Endpoint",
        summary={
            "mean": 45.2,
            "sd": 8.7,
            "ci_lower": 42.1,
            "ci_upper": 48.3,
            "n": 150,
            "p_value": 0.0023
        }
    )
)

print("\n--- Initial state:")
print(dtree1)

# First round: Create mean ± SD
format_statistics(dtree, inplace=True, format_spec="{mean:.1f} ± {sd:.1f}", stat_name="mean_sd")
print("\n--- After Round 1 (mean ± SD):")
print(dtree1)

# Second round: Create CI range
format_statistics(dtree, inplace=True, format_spec="({ci_lower:.1f}, {ci_upper:.1f})", stat_name="ci_range")
print("\n--- After Round 2 (CI range):")
print(dtree1)

# Third round: Combine mean_sd and ci_range
format_statistics(dtree, inplace=True, format_spec="{mean_sd}, 95% CI: {ci_range}", stat_name="full_summary")
print("\n--- After Round 3 (full summary):")
print(dtree1)

print("\nFinal formatted result:")
print(f"  {dtree1['endpoint1'].summary['full_summary']}")
print(f"  p-value: {dtree1['endpoint1'].summary['p_value']}")

# Example 2: Progressive formatting with removal
print("\n" + "=" * 70)
print("Example 2: Progressive Formatting (Remove Intermediate Results)")
print("=" * 70)

dtree2 = DataTree(
    endpoint2 = DataNode(
        label="Secondary Endpoint",
        summary={
            "mean": 32.8,
            "sd": 5.4,
            "ci_lower": 31.2,
            "ci_upper": 34.4,
            "n": 150,
            "p_value": 0.0451
        }
    )
)

print("\n--- Initial state:")
print(dtree2)

# Round 1: Create mean ± SD and remove originals
format_statistics(
    dtree2, 
    format_spec="{mean:.1f} ± {sd:.1f}", 
    stat_name="mean_sd",
    remove_original=True
)
print("\n--- After Round 1 (mean ± SD, originals removed):")
print(dtree2)

# Round 2: Create CI range and remove originals
format_statistics(
    dtree2,
    format_spec="({ci_lower:.1f}, {ci_upper:.1f})",
    stat_name="ci_range",
    remove_original=True
)
print("\n--- After Round 2 (CI range, originals removed):")
print(dtree2)

# Round 3: Combine into final format and remove intermediates
format_statistics(
    dtree2,
    format_spec="{mean_sd}, 95% CI: {ci_range}",
    stat_name="result",
    remove_original=True
)
print("\n--- After Round 3 (final result, intermediates removed):")
print(dtree2)

print("\nFinal state - only essential statistics remain:")
print(f"  Result: {dtree2['endpoint2'].summary['result']}")
print(f"  Sample size: {dtree2['endpoint2'].summary['n']}")
print(f"  p-value: {dtree2['endpoint2'].summary['p_value']}")

# Example 3: Mixed approach - complex nested tree
print("\n" + "=" * 70)
print("Example 3: Complex Nested Tree with Multiple Formatting Rounds")
print("=" * 70)

dtree3 = DataTree(
    by_treatment = SplitDataNode(
        split_var="Treatment",
        placebo=LvlDataNode(
            split_lvl="Placebo",
            baseline=DataNode(
                label="Baseline",
                summary={"mean": 42.3, "sd": 7.5, "min": 28.1, "max": 58.9, "n": 75}
            ),
            week_12=DataNode(
                label="Week 12",
                summary={"mean": 43.1, "sd": 7.8, "min": 29.2, "max": 59.4, "n": 72}
            )
        ),
        active=LvlDataNode(
            split_lvl="Active Treatment",
            baseline=DataNode(
                label="Baseline",
                summary={"mean": 41.8, "sd": 8.2, "min": 26.5, "max": 60.1, "n": 75}
            ),
            week_12=DataNode(
                label="Week 12",
                summary={"mean": 38.5, "sd": 7.1, "min": 24.8, "max": 54.2, "n": 73}
            )
        )
    )
)

print("\n--- Initial state:")
print(dtree3)

# Round 1: Create range (min-max)
print("\n--- Round 1: Creating ranges...")
format_statistics(dtree, inplace=True3, format_spec="[{min:.1f}, {max:.1f}]", stat_name="range")
print(dtree3)

# Round 2: Create mean ± SD, keeping range
print("\n--- Round 2: Creating mean ± SD...")
format_statistics(dtree, inplace=True3, format_spec="{mean:.1f} ± {sd:.1f}", stat_name="mean_sd")
print(dtree3)

# Round 3: Create final summary combining both, remove intermediates except n
print("\n--- Round 3: Creating final summary...")
format_statistics(
    dtree3,
    format_spec="{mean_sd} (range: {range})",
    stat_name="summary",
    remove_original=True
)
print(dtree3)

print("\nFinal formatted statistics:")
print(f"Placebo Baseline: {dtree3['by_treatment']['placebo']['baseline'].summary['summary']}")
print(f"  (n={dtree3['by_treatment']['placebo']['baseline'].summary['n']})")
print(f"Placebo Week 12: {dtree3['by_treatment']['placebo']['week_12'].summary['summary']}")
print(f"  (n={dtree3['by_treatment']['placebo']['week_12'].summary['n']})")
print(f"Active Baseline: {dtree3['by_treatment']['active']['baseline'].summary['summary']}")
print(f"  (n={dtree3['by_treatment']['active']['baseline'].summary['n']})")
print(f"Active Week 12: {dtree3['by_treatment']['active']['week_12'].summary['summary']}")
print(f"  (n={dtree3['by_treatment']['active']['week_12'].summary['n']})")

# Example 4: Label-specific multi-round formatting
print("\n" + "=" * 70)
print("Example 4: Label-Specific Multi-Round Formatting")
print("=" * 70)

dtree4 = DataTree(
    continuous_outcome = DataNode(
        label="Continuous",
        summary={"mean": 45.2, "sd": 8.7, "median": 44.1, "q1": 39.5, "q3": 50.2}
    ),
    binary_outcome = DataNode(
        label="Binary",
        summary={"n_events": 45, "n_total": 150, "pct": 30.0, "ci_lower": 23.1, "ci_upper": 37.8}
    )
)

print("\n--- Initial state:")
print(dtree4)

# Round 1: Create primary summaries for each type
print("\n--- Round 1: Creating type-specific primary summaries...")
format_statistics(
    dtree4,
    format_map={
        "Continuous": "{mean:.1f} ± {sd:.1f}",
        "Binary": "{n_events}/{n_total} ({pct:.1f}%)"
    },
    stat_name="primary"
)
print(dtree4)

# Round 2: Add secondary information
print("\n--- Round 2: Adding secondary information...")
format_statistics(
    dtree4,
    format_map={
        "Continuous": "{median:.1f} [{q1:.1f}-{q3:.1f}]",
        "Binary": "95% CI: {ci_lower:.1f}%-{ci_upper:.1f}%"
    },
    stat_name="secondary"
)
print(dtree4)

# Round 3: Combine into final format
print("\n--- Round 3: Creating comprehensive summary...")
format_statistics(
    dtree4,
    format_map={
        "Continuous": "Mean: {primary}, Median: {secondary}",
        "Binary": "{primary}, {secondary}"
    },
    stat_name="complete",
    remove_original=True
)
print(dtree4)

print("\nFinal comprehensive summaries:")
print(f"Continuous: {dtree4['continuous_outcome'].summary['complete']}")
print(f"Binary: {dtree4['binary_outcome'].summary['complete']}")

print("\n" + "=" * 70)
print("All multi-round formatting examples completed!")
print("=" * 70)

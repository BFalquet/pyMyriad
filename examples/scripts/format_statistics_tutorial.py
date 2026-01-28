"""
Example demonstrating the format_statistics function.

This script shows how to use format_statistics to combine multiple statistics
into formatted strings in DataNode objects.
"""

from pyMyriad import DataTree, DataNode, SplitDataNode, LvlDataNode, format_statistics

# Example 1: Global formatting
print("=" * 60)
print("Example 1: Global formatting")
print("=" * 60)

dtree1 = DataTree(
    overall = DataNode(
        label="Overall Mean", 
        summary={"m": 45.2, "sd": 8.7, "n": 150}
    ),
    baseline = DataNode(
        label="Baseline Mean", 
        summary={"m": 42.8, "sd": 9.1, "n": 150}
    )
)

print("\nBefore formatting:")
print(dtree1)

# Apply global format (modifies in place)
format_statistics(dtree1, format_spec="{m} ± {sd}", stat_name="mean_sd", inplace=True)

print("\nAfter formatting:")
print(dtree1)

print("\nFormatted values:")
print(f"Overall: {dtree1['overall'].summary['mean_sd']}")
print(f"Baseline: {dtree1['baseline'].summary['mean_sd']}")


# Example 2: Label-specific formatting
print("\n" + "=" * 60)
print("Example 2: Label-specific formatting")
print("=" * 60)

dtree2 = DataTree(
    mean_analysis = DataNode(
        label="Mean Analysis", 
        summary={"mean": 45.2, "sd": 8.7, "n": 150}
    ),
    median_analysis = DataNode(
        label="Median Analysis", 
        summary={"median": 44.5, "q1": 39.2, "q3": 51.8, "n": 150}
    )
)

print("\nBefore formatting:")
print(dtree2)

# Apply different formats for different labels
format_statistics(
    dtree2,
    format_map={
        "Mean Analysis": "{mean} (SD: {sd})",
        "Median Analysis": "{median} [IQR: {q1}-{q3}]"
    },
    stat_name="formatted_result",
    inplace=True
)

print("\nAfter formatting:")
print(dtree2)

print("\nFormatted values:")
print(f"Mean: {dtree2['mean_analysis'].summary['formatted_result']}")
print(f"Median: {dtree2['median_analysis'].summary['formatted_result']}")


# Example 3: Nested tree with formatting
print("\n" + "=" * 60)
print("Example 3: Nested tree structure")
print("=" * 60)

dtree3 = DataTree(
    by_group = SplitDataNode(
        split_var="Treatment Group",
        placebo=LvlDataNode(
            split_lvl="Placebo",
            baseline=DataNode(
                label="Baseline", 
                summary={"m": 42.3, "sd": 7.5}
            ),
            week_12=DataNode(
                label="Week 12", 
                summary={"m": 43.1, "sd": 7.8}
            )
        ),
        treatment=LvlDataNode(
            split_lvl="Treatment",
            baseline=DataNode(
                label="Baseline", 
                summary={"m": 41.8, "sd": 8.2}
            ),
            week_12=DataNode(
                label="Week 12", 
                summary={"m": 38.5, "sd": 7.1}
            )
        )
    )
)

print("\nBefore formatting:")
print(dtree3)

# Apply formatting with precision control
format_statistics(
    dtree3, 
    format_spec="{m:.1f} ± {sd:.1f}",
    stat_name="mean_sd",
    inplace=True
)

print("\nAfter formatting:")
print(dtree3)

print("\nFormatted values from nested structure:")
print(f"Placebo Baseline: {dtree3['by_group']['placebo']['baseline'].summary['mean_sd']}")
print(f"Placebo Week 12: {dtree3['by_group']['placebo']['week_12'].summary['mean_sd']}")
print(f"Treatment Baseline: {dtree3['by_group']['treatment']['baseline'].summary['mean_sd']}")
print(f"Treatment Week 12: {dtree3['by_group']['treatment']['week_12'].summary['mean_sd']}")


# Example 4: Mixed global and label-specific formatting
print("\n" + "=" * 60)
print("Example 4: Mixed formatting (global + label-specific)")
print("=" * 60)

dtree4 = DataTree(
    primary = DataNode(
        label="Primary Endpoint", 
        summary={"m": 12.5, "sd": 2.3, "ci_lower": 11.8, "ci_upper": 13.2}
    ),
    secondary = DataNode(
        label="Secondary Endpoint", 
        summary={"m": 8.7, "sd": 1.5, "ci_lower": 8.3, "ci_upper": 9.1}
    ),
    exploratory = DataNode(
        label="Exploratory", 
        summary={"m": 15.2, "sd": 4.1, "ci_lower": 13.5, "ci_upper": 16.9}
    )
)

print("\nBefore formatting:")
print(dtree4)

# Global format with override for primary endpoint
format_statistics(
    dtree4,
    format_spec="{m} ± {sd}",  # Default for all
    format_map={"Primary Endpoint": "{m} (95% CI: {ci_lower}-{ci_upper})"},  # Special for primary
    stat_name="display",
    inplace=True
)

print("\nAfter formatting:")
print(dtree4)

print("\nFormatted values:")
print(f"Primary: {dtree4['primary'].summary['display']}")
print(f"Secondary: {dtree4['secondary'].summary['display']}")
print(f"Exploratory: {dtree4['exploratory'].summary['display']}")

print("\n" + "=" * 60)
print("All examples completed successfully!")
print("=" * 60)

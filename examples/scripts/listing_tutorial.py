"""
Tutorial: Using the Enhanced Listing Functionality in pyMyriad

This tutorial demonstrates the improved listing features that make
hierarchical analysis results easier to read and understand.
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '../../src')

from pyMyriad import AnalysisTree, simple_table, gt_table

# Create sample data
np.random.seed(42)
df = pd.DataFrame({
    "id": np.arange(100),
    "Gender": np.random.choice(["M", "F"], 100),
    "Country": np.random.choice(["US", "UK", "Canada"], 100),
    "Age": np.random.randint(18, 70, 100),
    "Income": np.random.normal(50000, 15000, 100),
    "Education_Years": np.random.randint(10, 20, 100),
})

print("=" * 80)
print("EXAMPLE 1: Basic Hierarchical Analysis")
print("=" * 80)
print("\nAnalyzing income by Gender and Country...\n")

# Create a hierarchical analysis tree
atree = AnalysisTree()\
    .split_by("df.Gender")\
    .split_by("df.Country")\
    .analyze_by(
        mean_income=lambda df: np.mean(df.Income),
        std_income=lambda df: np.std(df.Income),
        count=lambda df: len(df)
    )

# Run the analysis
dtree = atree.run(df)

# Display results with hierarchical columns
result = simple_table(dtree)
print(result.to_string())

print("\n" + "=" * 80)
print("EXAMPLE 2: Analysis with Pivot")
print("=" * 80)
print("\nPivoting by Gender to compare side-by-side...\n")

# Same analysis but pivoted by Gender
result_pivot = simple_table(dtree, by="df.Gender")
print(result_pivot.to_string())

print("\n" + "=" * 80)
print("EXAMPLE 3: Multi-Level Analysis with Summarize")
print("=" * 80)
print("\nAdding intermediate summaries at each level...\n")

# Create analysis with intermediate summaries
atree2 = AnalysisTree()\
    .split_by("df.Gender")\
    .summarize_by(
        gender_mean=lambda df: np.mean(df.Income),
        gender_count=lambda df: len(df)
    )\
    .split_by("df.Country")\
    .analyze_by(
        country_mean=lambda df: np.mean(df.Income),
        country_std=lambda df: np.std(df.Income),
        country_count=lambda df: len(df)
    )

dtree2 = atree2.run(df)
result2 = simple_table(dtree2)
print(result2.to_string())

print("\n" + "=" * 80)
print("EXAMPLE 4: Simple Analysis (No Splits)")
print("=" * 80)
print("\nOverall statistics without grouping...\n")

# Analysis without splits
atree3 = AnalysisTree()\
    .analyze_by(
        mean_income=lambda df: np.mean(df.Income),
        median_income=lambda df: np.median(df.Income),
        std_income=lambda df: np.std(df.Income),
        min_income=lambda df: np.min(df.Income),
        max_income=lambda df: np.max(df.Income),
        count=lambda df: len(df)
    )

dtree3 = atree3.run(df)
result3 = simple_table(dtree3)
print(result3.to_string())

print("\n" + "=" * 80)
print("EXAMPLE 5: Three-Level Hierarchy")
print("=" * 80)
print("\nAnalyzing by Gender, Country, and Age Group...\n")

# Three-level hierarchy
atree4 = AnalysisTree()\
    .split_by("df.Gender")\
    .split_by("df.Country")\
    .split_by(
        young="df.Age < 35",
        middle="(df.Age >= 35) & (df.Age < 55)",
        senior="df.Age >= 55"
    )\
    .analyze_by(
        mean_income=lambda df: np.mean(df.Income),
        count=lambda df: len(df)
    )

dtree4 = atree4.run(df)
result4 = simple_table(dtree4)
print(result4.to_string())

print("\n" + "=" * 80)
print("EXAMPLE 6: Including Non-Analysis Rows")
print("=" * 80)
print("\nShowing all tree nodes including splits and levels...\n")

# Show all rows including non-analysis
result5 = simple_table(dtree, include_non_analysis=True)
print(result5.head(20).to_string())
print(f"\n... ({len(result5)} total rows)")

print("\n" + "=" * 80)
print("EXAMPLE 7: Without Path Splitting")
print("=" * 80)
print("\nDisabling hierarchical column splitting...\n")

# Without splitting paths into levels
result6 = simple_table(dtree, split_path=False)
print(result6.to_string())

print("\n" + "=" * 80)
print("KEY FEATURES OF THE NEW LISTING FUNCTIONALITY")
print("=" * 80)
print("""
1. HIERARCHICAL COLUMNS: Paths are automatically split into Level_0, Level_1, 
   Level_2, etc., making it easy to see the analysis structure.

2. CLEAN LABELS: 'df.' prefixes are removed, and 'root' and 'analysis' markers
   are hidden for cleaner display.

3. PIVOT SUPPORT: Use the 'by' parameter to pivot results by any split variable,
   creating side-by-side comparisons.

4. FLEXIBLE DISPLAY: Control what's shown with:
   - include_non_analysis: Show/hide intermediate tree nodes
   - split_path: Enable/disable hierarchical column splitting

5. SIMPLE_TABLE vs GT_TABLE:
   - simple_table(): Returns a pandas DataFrame (no dependencies)
   - gt_table(): Returns a formatted Great Tables object (requires great-tables)

6. MULTI-LEVEL ANALYSES: Properly handles both terminal analyses (.analyze_by)
   and intermediate summaries (.summarize_by) at different tree levels.
""")

print("\n" + "=" * 80)
print("COMPARISON: Old vs New Path Display")
print("=" * 80)
print("""
OLD (single path column):
  Path                              | Statistic    | Value
  Gender > F > Country > UK         | mean_income  | 77500.0
  Gender > F > Country > US         | mean_income  | 70000.0

NEW (hierarchical columns):
  Level_0 | Level_1 | Level_2 | Level_3 | Statistic    | Value
  Gender  | F       | Country | UK      | mean_income  | 77500.0
  Gender  | F       | Country | US      | mean_income  | 70000.0

Benefits:
- Easier to filter and sort by specific hierarchy levels
- Better alignment and readability
- Natural grouping in spreadsheet applications
- Clearer understanding of the analysis structure
""")

print("\nTutorial complete!")

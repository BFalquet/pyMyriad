"""
Tutorial: Using the Enhanced Listing Functionality in pyMyriad

This tutorial demonstrates the improved listing features that make
hierarchical analysis results easier to read and understand.
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '../../src')

from pyMyriad import AnalysisTree, simple_table, cascade_table, gt_table

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

# Create a hierarchical analysis tree
atree = AnalysisTree()\
    .split_by("df.Gender")\
    .summarize_by(mean_income=lambda df: np.mean(df.Income))\
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

# Same analysis but pivoted by Country
result_pivot = simple_table(dtree, by="df.Country")
print(result_pivot.to_string())

print("\n" + "=" * 80)
print("EXAMPLE 3: Multi-Level Analysis with Summarize")
print("=" * 80)
print("\nAdding intermediate summaries at each level...\n")

# Create analysis with intermediate summaries
atree2 = AnalysisTree()\
    .split_by("df.Gender")\
    .split_at_root_by("df.Education_Years")\
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
print("EXAMPLE 6: Including Non-Analysis Rows (cascade_table)")
print("=" * 80)
print("\nShowing all tree nodes including splits and levels using cascade_table()...\n")

# Show all rows including non-analysis using cascade_table
result5 = cascade_table(dtree)
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
print("EXAMPLE 8: Duplicate Suppression")
print("=" * 80)
print("\nBy default, consecutive duplicate values are suppressed for cleaner display:\n")

result_suppress = simple_table(dtree, suppress_duplicates=True)
print("WITH suppression (default):")
print(result_suppress.head(10).to_string())

print("\n\nWITHOUT suppression:")
result_no_suppress = simple_table(dtree, suppress_duplicates=False)
print(result_no_suppress.head(10).to_string())

print("\n" + "=" * 80)
print("KEY FEATURES OF THE NEW LISTING FUNCTIONALITY")
print("=" * 80)
print("""
1. HIERARCHICAL COLUMNS: Paths are automatically split into Level_0, Level_1, 
   Level_2, etc., making it easy to see the analysis structure.

2. CLEAN LABELS: 'df.' prefixes are removed, and 'root' and 'analysis' markers
   are hidden for cleaner display.

3. DUPLICATE SUPPRESSION: Consecutive duplicate values in hierarchy columns are
   automatically suppressed (shown as empty) for cleaner, more readable tables.

4. SMART PIVOT: Use the 'by' parameter to pivot results by any split variable.
   The pivoted level is automatically removed, and rows are properly combined
   for side-by-side comparisons.

5. NO REDUNDANT COLUMNS: The 'Analysis' column is removed since it only shows
   "Analysis" for all rows.

6. FLEXIBLE DISPLAY: Control what's shown with:
   - cascade_table(): Show all tree nodes (splits, summaries, analyses)
   - split_path: Enable/disable hierarchical column splitting
   - suppress_duplicates: Enable/disable duplicate suppression

7. SIMPLE_TABLE vs CASCADE_TABLE vs GT_TABLE:
   - simple_table(): Returns a pandas DataFrame with only analysis results
   - cascade_table(): Returns a pandas DataFrame with all tree nodes
   - gt_table(): Returns a formatted Great Tables object (requires great-tables)

8. MULTI-LEVEL ANALYSES: Properly handles both terminal analyses (.analyze_by)
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

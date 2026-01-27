import pandas as pd
import numpy as np
from pyMyriad import *
from pyMyriad.tabular import flatten

# Set random seed for reproducibility
np.random.seed(42)

df = pd.DataFrame({
  "id": np.arange(1000),
  "Gender": np.random.choice(["M", "F"], 1000),
  "Age": np.random.randint(18, 70, 1000),
  "Income": np.random.normal(50000, 15000, 1000),
  "Country": np.random.choice(["Benin", "Albania"], 1000),
  "Education": np.random.normal(0, 1, 1000),
  "Employed": np.random.choice([0, 1], 1000)
})

mfun = lambda df: np.mean(df.Income)
nfun = lambda df: np.std(df.Income)
efun = lambda df: np.mean(df.Education)
benin_fun =  lambda df: df.Country == 'Benin'
age_40 = lambda df: df.Age > 40
age_60 = lambda df: df.Age > 60

atree = AnalysisTree()\
  .split_by("df.Gender")\
  .summarize_by(m = mfun, n = nfun)\
  .split_by(label = "Benin Y/N", expr = benin_fun)\
  .split_by(label = "Age Group", age40 = age_40, age60 = age_60)\
  .analyze_by(m = mfun, n = nfun, label = "Income analysis")\
  .analyze_by(m = efun, label = "Education analysis")

res = atree.run(df)

# ============================================================================
# DEMONSTRATION OF NEW LISTING FUNCTIONALITY
# ============================================================================

print("=" * 80)
print("HIERARCHICAL TABLE VIEW (using simple_table)")
print("=" * 80)
print("\nThis shows the analysis results with hierarchical columns:")
print("Level_0, Level_1, Level_2, etc. represent different levels of grouping\n")

# Display results with hierarchical columns
table = simple_table(res)
print(table.to_string())

print("\n" + "=" * 80)
print("PIVOTED VIEW BY GENDER")
print("=" * 80)
print("\nSame data pivoted by Gender for side-by-side comparison:\n")

# Pivot by Gender
table_pivot = simple_table(res, by="df.Gender")
print(table_pivot.head(20).to_string())
print(f"\n... ({len(table_pivot)} total rows)")

print("\n" + "=" * 80)
print("TRADITIONAL FLATTEN VIEW (for comparison)")
print("=" * 80)
print("\nThe old flatten() function still works:\n")

# Traditional flatten for comparison
flat = flatten(res, unnest=True)
print(flat[['path', 'type', 'label', 'statistics', 'values']].head(10).to_string())
print(f"\n... ({len(flat)} total rows)")

# Uncomment to see plots
# forest_plot(res, x = "m", x_err="n", type = "forest", col = "Benin Y/N", jitter = True)

# from pyMyriad.plots import distribution_plot
# distribution_plot(
#     res, 
#     x={"Unlabelled": "Age", "Income analysis": "Income", "Education analysis": "Education"}, 
#     col="Benin Y/N", 
#     type="violin", 
#     jitter=True
# )


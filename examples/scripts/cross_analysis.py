
from pyMyriad import AnalysisTree
import pandas as pd
import numpy as np


# Set random seed for reproducibility
np.random.seed(42)

df = pd.DataFrame({
    "id": np.arange(100),
    "Gender": np.random.choice(["M", "F"], 100),
    "Country": np.random.choice(["US", "UK", "Canada"], 100),
    "Age": np.random.randint(18, 70, 100),
    "Income": np.random.normal(50000, 15000, 100),
    "Education_Years": np.random.randint(10, 20, 100),
})

# Create a hierarchical analysis tree with cross-analysis
# Cross-analysis compares each country's statistics against a reference (US)
atree = AnalysisTree()\
    .split_by("df.Gender")\
    .summarize_by(mean_income="np.mean(df.Income)")\
    .split_by("df.Country")\
    .cross_analyze_by(
        ref_lvl="US",
        # Compare mean income between current group (df) and reference group (ref_df)
        mean_income_diff="np.mean(df.Income) - np.mean(ref_df.Income)",
        # Compare standard deviation of income
        std_income_diff="np.std(df.Income) - np.std(ref_df.Income)"
    )

print(atree)

res = atree.run(df)

print(res)
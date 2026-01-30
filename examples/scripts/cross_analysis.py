
from pyMyriad import AnalysisTree, simple_table, gt_table
import pandas as pd
import numpy as np


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
    .summarize_by(mean_income="0")\
    .split_by("df.Country")\
    .cross_analyze_by(
        ref_lvl="US",
        mean_income_diff="10",
        std_income_diff="11"
    )

print(atree)

res = atree.run(df)

print(res)
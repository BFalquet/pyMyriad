"""Build a demographics / baseline-characteristics ("Table 1") table with
summary_table() (#76).

Columns are treatment Arm; rows are a list of variables, each summarized
per its declared type — continuous (n / Mean (SD) / Median (Q1, Q3) /
Min-Max) or categorical (one row per level, "n (pct%)" of the arm total).
An optional `by=` column stratifies the whole table into row blocks (here,
one block per sex).

Run with:
    uv run python examples/summary_table_demo.py
"""

import numpy as np
import pandas as pd

from pyMyriad.clinical import summary_table

# ---------------------------------------------------------------------------
# 1. Simulate subject-level baseline data: one row per subject.
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)

ARMS = ["Placebo", "Active 10 mg"]
SEXES = ["Male", "Female"]
ETHNICITIES = ["White", "Black", "Other"]
N_SUBJECTS = 60

df = pd.DataFrame(
    {
        "USUBJID": [f"S{i:03d}" for i in range(N_SUBJECTS)],
        "ARM": pd.Categorical(
            rng.choice(ARMS, size=N_SUBJECTS), categories=ARMS, ordered=True
        ),
        "SEX": pd.Categorical(
            rng.choice(SEXES, size=N_SUBJECTS), categories=SEXES, ordered=True
        ),
        "AGE": rng.normal(50, 10, size=N_SUBJECTS).round(0),
        "ETHNIC": rng.choice(ETHNICITIES, size=N_SUBJECTS, p=[0.6, 0.25, 0.15]),
    }
)

# ---------------------------------------------------------------------------
# 2. Build the table in one call, stratified by SEX.
# ---------------------------------------------------------------------------
table = summary_table(
    df,
    variables={"AGE": "continuous", "ETHNIC": "categorical"},
    arm_col="ARM",
    subject_col="USUBJID",
    by="SEX",
)

print("=== Baseline Characteristics by Sex and Treatment Arm ===")
print(table.to_string(index=False))

# ---------------------------------------------------------------------------
# 3. Great Tables (HTML) version, with a bold row group per sex.
# ---------------------------------------------------------------------------
gt = summary_table(
    df,
    variables={"AGE": "continuous", "ETHNIC": "categorical"},
    arm_col="ARM",
    subject_col="USUBJID",
    by="SEX",
    as_gt=True,
    title="Baseline Characteristics",
)

out_path = "examples/out/summary_table_demo.html"
with open(out_path, "w") as f:
    f.write(gt.as_raw_html())
print(f"\nSaved HTML table to {out_path}")

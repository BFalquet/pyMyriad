"""Build the canonical clinical-trial lab table with lab_summary_table() (#65).

Compare this to a hand-rolled version of the same table: a per-subject
baseline lookup closure, eight separately-named formatted statistics in one
analyze_by() call, an Arm pivot, and a hand-rolled wide-to-long pd.concat
reshape. lab_summary_table() wraps all of that behind a single call.

Run with:
    uv run python examples/lab_summary_table_demo.py
"""

import numpy as np
import pandas as pd

from pyMyriad.clinical import lab_summary_table

# ---------------------------------------------------------------------------
# 1. Simulate CDISC-like lab data: one row per subject per visit.
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)

ARMS = ["Placebo", "Active 10 mg"]
VISITS = ["Baseline", "Week 4", "Week 8", "Week 12"]
N_SUBJECTS = 40

subjects = pd.DataFrame(
    {
        "USUBJID": [f"S{i:03d}" for i in range(N_SUBJECTS)],
        "ARM": rng.choice(ARMS, size=N_SUBJECTS),
    }
)

rows = []
for subj in subjects.itertuples():
    baseline = rng.normal(45, 8)
    drift = -6 if subj.ARM == "Active 10 mg" else -1  # active arm trends down
    for visit_idx, visit in enumerate(VISITS):
        aval = baseline + drift * visit_idx / 3 + rng.normal(0, 3)
        rows.append(
            {"USUBJID": subj.USUBJID, "ARM": subj.ARM, "AVISIT": visit, "AVAL": aval}
        )

df = pd.DataFrame(rows)
df["AVISIT"] = pd.Categorical(df["AVISIT"], categories=VISITS, ordered=True)
df["ARM"] = pd.Categorical(df["ARM"], categories=ARMS, ordered=True)

# ---------------------------------------------------------------------------
# 2. Build the table in one call.
# ---------------------------------------------------------------------------
table = lab_summary_table(
    df,
    value_col="AVAL",
    visit_col="AVISIT",
    arm_col="ARM",
    subject_col="USUBJID",
    baseline_level="Baseline",
)

print("=== ALT (U/L) by Visit and Treatment Arm ===")
print(table.to_string(index=False))

# ---------------------------------------------------------------------------
# 3. Great Tables (HTML) version.
# ---------------------------------------------------------------------------
gt = lab_summary_table(
    df,
    value_col="AVAL",
    visit_col="AVISIT",
    arm_col="ARM",
    subject_col="USUBJID",
    baseline_level="Baseline",
    as_gt=True,
    title="ALT (U/L) by Visit and Treatment Arm",
)

out_path = "examples/out/lab_summary_table_demo.html"
with open(out_path, "w") as f:
    f.write(gt.as_raw_html())
print(f"\nSaved HTML table to {out_path}")

"""Classic clinical-trial lab table: value and change from baseline by visit and arm.

Reproduces the standard "Summary of Laboratory Values and Change from Baseline
by Visit and Treatment Group" table seen in clinical study reports:

    Visit       Placebo                         Active 10 mg
                n     Value        Change           n     Value        Change
    Baseline    20    47.2 (7.5)   0.0 (0.0)        20    45.2 (8.3)   0.0 (0.0)
    Week 4      20    46.1 (7.9)  -1.2 (3.9)        20    43.5 (6.9)  -1.7 (3.9)
    ...

Rows are visits, columns are treatment arms each subdivided into the
observed value and the change from baseline.

Key idea: "change from baseline" is a per-subject quantity (each subject's
value at a visit minus that *same subject's* baseline value). pyMyriad's
AnalysisTree only sees the rows belonging to the current split (visit x arm),
so the per-subject baseline must be merged onto every row *before* the tree
runs. The tree itself then just averages the precomputed ``Change`` column,
the same way it averages the raw value.
"""

import numpy as np
import pandas as pd

from pyMyriad import AnalysisTree, format_statistics, simple_table

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

# ---------------------------------------------------------------------------
# 2. Precompute change from baseline per subject, per visit.
# ---------------------------------------------------------------------------
baseline_vals = df.loc[df.AVISIT == "Baseline", ["USUBJID", "AVAL"]].rename(
    columns={"AVAL": "BASE"}
)
df = df.merge(baseline_vals, on="USUBJID", how="left")
df["CHG"] = df["AVAL"] - df["BASE"]

# ---------------------------------------------------------------------------
# 3. Build the analysis tree: rows = Visit, columns (pivoted later) = Arm.
# ---------------------------------------------------------------------------
tree = (
    AnalysisTree()
    .split_by("df.AVISIT", label="Visit")
    .split_by("df.ARM", label="Arm")
    .analyze_by(
        n=lambda df: len(df),
        mean=lambda df: np.mean(df.AVAL),
        sd=lambda df: np.std(df.AVAL, ddof=1),
        mean_chg=lambda df: np.mean(df.CHG),
        sd_chg=lambda df: np.std(df.CHG, ddof=1),
    )
)
result = tree.run(df)

# ---------------------------------------------------------------------------
# 4. Combine raw stats into presentation strings ("mean (sd)").
#    Keys are prefixed "01_/02_/03_" purely so that simple_table/gt_table's
#    alphabetical column pivot lands in n -> value -> change order; the
#    prefix is stripped again when relabeling the gt_table below.
# ---------------------------------------------------------------------------
formatted = format_statistics(
    result,
    **{
        "01_n": "{n}",
        "02_value": "{mean:.1f} ({sd:.1f})",
        "03_change": "{mean_chg:.1f} ({sd_chg:.1f})",
    },
    remove_original=True,
)

# ---------------------------------------------------------------------------
# 5a. Plain pandas version: pivot Arm to columns, each subdivided by statistic.
# ---------------------------------------------------------------------------
table = simple_table(formatted, by="Arm", pivot_statistics=True)

# Row order follows the alphabetical pivot of AVISIT; restore chronological order.
visit_order = {v: i for i, v in enumerate(VISITS)}
table = (
    table.sort_values("_Level_1", key=lambda s: s.map(visit_order))
    .reset_index(drop=True)
    .drop(columns=["_Level_0"])
    .rename(columns={"_Level_1": "Visit"})
)
table.columns = [
    c.replace("||01_n", " n")
    .replace("||02_value", " Value, Mean (SD)")
    .replace("||03_change", " Change from Baseline, Mean (SD)")
    for c in table.columns
]

print("=== ALT (U/L) by Visit and Treatment Arm ===")
print(table.to_string(index=False))

# ---------------------------------------------------------------------------
# 5b. Great Tables (HTML) version: same `table`, with arm spanners over
#     n / Value / Change. Built from the already row- and column-ordered
#     pandas table for full control (gt_table(by=..., pivot_statistics=True)
#     is a quicker one-liner equivalent of 5a, but pivots both rows and
#     columns alphabetically, which loses the chronological visit order).
# ---------------------------------------------------------------------------
from great_tables import GT  # noqa: E402

arm_columns = {arm: [c for c in table.columns if c.startswith(arm)] for arm in ARMS}

gt = GT(table).tab_header(
    title="ALT (U/L) by Visit and Treatment Arm",
    subtitle="Mean (SD); Change from Baseline = Visit value - Baseline value",
)
for arm, cols in arm_columns.items():
    gt = gt.tab_spanner(label=arm, columns=cols)
gt = gt.cols_label(**{c: c[len(arm) + 1 :] for arm, cols in arm_columns.items() for c in cols})
gt = gt.cols_align(align="center", columns=[c for cols in arm_columns.values() for c in cols])

out_path = "examples/out/lab_change_from_baseline_table.html"
with open(out_path, "w") as f:
    f.write(gt.as_raw_html())
print(f"\nSaved HTML table to {out_path}")

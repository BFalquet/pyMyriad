"""Clinical-trial lab table with multiple descriptive-statistic rows per visit.

Extends lab_change_from_baseline_table_v2.py: instead of a single "Mean (SD)"
row per visit, each visit now has four rows - n, Mean (SD), Median (Q1, Q3),
and Min/Max - while columns stay Arm > {Value, Change from Baseline}, exactly
as before.

AnalysisTree itself has no notion of "put this statistic on a different row":
a tree node produces one set of named statistics per (Visit, Arm) leaf, and
pyMyriad's pivot machinery turns *one* split (here, Arm) into columns. Turning
some of those statistics into extra *rows* instead is a reshape that happens
after the tree has run - there is no tree-side primitive for it. So the
approach here is:

1. Compute every statistic (n, mean/sd, median/iqr, min/max - each for both
   the observed value and the change from baseline) as its own named,
   pre-formatted entry in a single analyze_by() call, same as v2.
2. Pivot Arm to columns as before, giving one row per Visit with all the
   statistics side by side as columns (Placebo||value_mean_sd, etc).
3. Reshape that wide row-per-visit table into a long row-per-(Visit,
   Statistic) table with plain pandas (pd.concat of one block per statistic
   group), which is what genuinely needs a "different row".
"""

import numpy as np
import pandas as pd
from great_tables import GT

from pyMyriad import AnalysisTree, simple_table

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

baseline_lookup = df.loc[df.AVISIT == "Baseline"].set_index("USUBJID")["AVAL"]


def _change(df: pd.DataFrame) -> pd.Series:
    return df.AVAL - df.USUBJID.map(baseline_lookup)


def _mean_sd(x: pd.Series) -> str:
    return f"{np.mean(x):.1f} ({np.std(x, ddof=1):.1f})"


def _median_iqr(x: pd.Series) -> str:
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    return f"{med:.1f} ({q1:.1f}, {q3:.1f})"


def _min_max(x: pd.Series) -> str:
    return f"{np.min(x):.1f}, {np.max(x):.1f}"


# ---------------------------------------------------------------------------
# 2. Build the analysis tree: every (value, change) x (n, mean/sd,
#    median/iqr, min/max) combination is its own named, formatted statistic.
#    "value_n"/"change_n" are identical (n doesn't depend on value vs.
#    change) - both are computed so every statistic group has the same
#    Value/Change column shape once reshaped in step 4.
# ---------------------------------------------------------------------------
tree = (
    AnalysisTree()
    .split_by("df.AVISIT", label="Visit")
    .split_by("df.ARM", label="Arm")
    .analyze_by(
        **{
            "value_n": lambda df: len(df),
            "change_n": lambda df: len(df),
            "value_mean_sd": lambda df: _mean_sd(df.AVAL),
            "change_mean_sd": lambda df: _mean_sd(_change(df)),
            "value_median_iqr": lambda df: _median_iqr(df.AVAL),
            "change_median_iqr": lambda df: _median_iqr(_change(df)),
            "value_min_max": lambda df: _min_max(df.AVAL),
            "change_min_max": lambda df: _min_max(_change(df)),
        },
        label="Lab Summary",
    )
)
result = tree.run(df)

# ---------------------------------------------------------------------------
# 3. Pivot Arm to columns: one row per Visit, with all eight statistics
#    available as "Arm||stat_name" columns.
# ---------------------------------------------------------------------------
wide = simple_table(result, by="Arm", pivot_statistics=True)

visit_order = {v: i for i, v in enumerate(VISITS)}
wide = (
    wide.sort_values("_Level_1", key=lambda s: s.map(visit_order))
    .reset_index(drop=True)
    .drop(columns=["_Level_0"])
    .rename(columns={"_Level_1": "Visit"})
)

# ---------------------------------------------------------------------------
# 4. Reshape wide -> long: one statistic group per row, stacked under each
#    Visit. This is the actual "different row" step - plain pandas, since
#    the tree/pivot machinery only pivots one axis (Arm) into columns.
# ---------------------------------------------------------------------------
STAT_ROWS = [
    ("n", "n"),
    ("Mean (SD)", "mean_sd"),
    ("Median (Q1, Q3)", "median_iqr"),
    ("Min, Max", "min_max"),
]

blocks = []
for stat_label, stat_key in STAT_ROWS:
    block = {"Visit": wide["Visit"], "Statistic": stat_label}
    for arm in ARMS:
        block[f"{arm}||Value"] = wide[f"{arm}||value_{stat_key}"]
        block[f"{arm}||Change"] = wide[f"{arm}||change_{stat_key}"]
    blocks.append(pd.DataFrame(block))

table = pd.concat(blocks, ignore_index=True)

stat_order = {stat_label: i for i, (stat_label, _) in enumerate(STAT_ROWS)}
table = table.sort_values(
    ["Visit", "Statistic"],
    key=lambda s: s.map(visit_order) if s.name == "Visit" else s.map(stat_order),
).reset_index(drop=True)
table = table[["Visit", "Statistic"] + [f"{arm}||{v}" for arm in ARMS for v in ("Value", "Change")]]

print("=== ALT (U/L) by Visit and Treatment Arm ===")
print(table.to_string(index=False))

# ---------------------------------------------------------------------------
# 5. Great Tables (HTML) version: arm spanners over Value/Change, and the
#    repeated Visit label suppressed for the 3 extra rows per visit.
# ---------------------------------------------------------------------------
display_table = table.copy()
display_table.loc[display_table["Visit"].duplicated(), "Visit"] = ""

arm_columns = {
    arm: [c for c in display_table.columns if c.startswith(f"{arm}||")] for arm in ARMS
}

gt = GT(display_table).tab_header(
    title="ALT (U/L) by Visit and Treatment Arm",
    subtitle="n; Mean (SD); Median (Q1, Q3); Min, Max - Value and Change from Baseline",
)
for arm, cols in arm_columns.items():
    gt = gt.tab_spanner(label=arm, columns=cols)
gt = gt.cols_label(**{c: c.split("||", 1)[1] for cols in arm_columns.values() for c in cols})
gt = gt.cols_align(align="center", columns=[c for cols in arm_columns.values() for c in cols])

out_path = "examples/out/lab_change_from_baseline_table_v3.html"
with open(out_path, "w") as f:
    f.write(gt.as_raw_html())
print(f"\nSaved HTML table to {out_path}")

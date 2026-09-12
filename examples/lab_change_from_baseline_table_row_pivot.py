"""Rebuild lab_change_from_baseline_table_v3.py's table using row_pivot (#62).

v3.py computes every (Value/Change) x (n, mean_sd, median_iqr, min_max)
combination as its own *pre-formatted string* statistic in analyze_by(), then
hand-rolls a pd.concat() of one block per statistic group to turn the wide
"Arm||stat" table into the long, row-per-statistic table actually wanted
(step 4 there - the part row_pivot replaces).

With row_pivot, analyze_by() only needs to compute *raw* numbers (mean, sd,
median, q1, q3, min, max) - a single row_pivot mapping then combines/labels/
orders them into rows directly inside simple_table().

row_pivot itself only pivots one column dimension at a time, and "Value" vs
"Change from Baseline" isn't a tree split - both are computed from the same
rows, just with a different metric. The trick used here: reshape the data
into "long" form with a literal MEASURE column (Value/Change), so it becomes
a real, poolable split - then pivot it *together* with Arm via
by=["Arm", "Measure"]. That gives one tree, one analyze_by() call, and one
simple_table(row_pivot=...) call for the whole table.

Run with:
    uv run python examples/lab_change_from_baseline_table_row_pivot.py
"""

import numpy as np
import pandas as pd
from great_tables import GT

from pyMyriad import AnalysisTree, simple_table

# ---------------------------------------------------------------------------
# 1. Simulate the same CDISC-like lab data as lab_change_from_baseline_table_v3.py.
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

baseline_lookup = df.loc[df.AVISIT == "Baseline"].set_index("USUBJID")["AVAL"]
df["CHANGE"] = df.AVAL - df.USUBJID.map(baseline_lookup)

# ---------------------------------------------------------------------------
# 2. Reshape to long form: one literal MEASURE column (Value/Change) holding
#    whichever metric applies, instead of two parallel sets of columns. This
#    turns "Value vs Change" into a real, poolable split alongside Arm.
# ---------------------------------------------------------------------------
long_df = pd.concat(
    [
        df.assign(METRIC=df.AVAL, MEASURE="Value"),
        df.assign(METRIC=df.CHANGE, MEASURE="Change"),
    ],
    ignore_index=True,
)
long_df["MEASURE"] = pd.Categorical(
    long_df["MEASURE"], categories=["Value", "Change"], ordered=True
)

# ---------------------------------------------------------------------------
# 3. One tree, one analyze_by() call computing raw statistics on METRIC -
#    row_pivot will combine/format/order them later.
# ---------------------------------------------------------------------------
tree = (
    AnalysisTree()
    .split_by("df.AVISIT", label="Visit")
    .split_by("df.ARM", label="Arm")
    .split_by("df.MEASURE", label="Measure")
    .analyze_by(
        n=lambda df: len(df),
        mean=lambda df: round(np.mean(df.METRIC), 1),
        sd=lambda df: round(np.std(df.METRIC, ddof=1), 1),
        median=lambda df: round(np.median(df.METRIC), 1),
        q1=lambda df: round(np.percentile(df.METRIC, 25), 1),
        q3=lambda df: round(np.percentile(df.METRIC, 75), 1),
        min=lambda df: round(np.min(df.METRIC), 1),
        max=lambda df: round(np.max(df.METRIC), 1),
    )
)
result = tree.run(long_df)

# ---------------------------------------------------------------------------
# 4. Pivot Arm and Measure together: columns come out named
#    "{Arm} > {Measure}", e.g. "Placebo > Value", "Placebo > Change". One
#    row_pivot mapping stacks n / Mean (SD) / Median (Q1, Q3) / Min, Max as
#    rows, combined per "{Arm} > {Measure}" column.
# ---------------------------------------------------------------------------
table = simple_table(
    result,
    by=["Arm", "Measure"],
    pivot_statistics=True,
    row_pivot={
        "n": ["n"],
        "Mean (SD)": lambda mean, sd: f"{mean} ({sd})",
        "Median (Q1, Q3)": lambda median, q1, q3: f"{median} ({q1}, {q3})",
        "Min, Max": lambda min, max: f"{min}, {max}",
    },
)
table = table.drop(columns=["_Level_0"]).rename(columns={"_Level_1": "Visit"})
table = table.rename(
    columns={c: c.replace(" > ", "||") for c in table.columns if " > " in c}
)
table = table[
    ["Visit", "Statistic"]
    + [f"{arm}||{measure}" for arm in ARMS for measure in ("Value", "Change")]
]

print(
    "=== ALT (U/L) by Visit and Treatment Arm (built with row_pivot, single tree) ==="
)
print(table.to_string(index=False))

# ---------------------------------------------------------------------------
# 5. Great Tables (HTML) version: arm spanners over Value/Change, matching
#    lab_change_from_baseline_table_v3.py's presentation.
# ---------------------------------------------------------------------------
display_table = table.copy()
display_table.loc[display_table["Visit"].duplicated(), "Visit"] = ""

arm_columns = {
    arm: [c for c in display_table.columns if c.startswith(f"{arm}||")] for arm in ARMS
}

gt = GT(display_table).tab_header(
    title="ALT (U/L) by Visit and Treatment Arm",
    subtitle="n; Mean (SD); Median (Q1, Q3); Min, Max - Value and Change from Baseline, built with row_pivot",
)
for arm, cols in arm_columns.items():
    gt = gt.tab_spanner(label=arm, columns=cols)
gt = gt.cols_label(
    **{c: c.split("||", 1)[1] for cols in arm_columns.values() for c in cols}
)
gt = gt.cols_align(
    align="center", columns=[c for cols in arm_columns.values() for c in cols]
)

out_path = "examples/out/lab_change_from_baseline_table_row_pivot.html"
with open(out_path, "w") as f:
    f.write(gt.as_raw_html())
print(f"\nSaved HTML table to {out_path}")

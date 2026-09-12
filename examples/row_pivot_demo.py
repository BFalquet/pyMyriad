"""Demo of row_pivot: stack a subset of statistics as rows instead of columns (#62).

Background: pivot_statistics=True always turns *every* named statistic into
its own column. That's awkward for a classic clinical descriptive-statistics
layout where one split (here, Arm) should stay pivoted into columns while a
*subset* of statistics - n, Mean (SD), Median (Q1, Q3), Min/Max - should each
get their own row under every Visit. Before row_pivot existed, building this
required computing the table fully wide and then manually reshaping it with
pd.concat() (see lab_change_from_baseline_table_v3.py, step 4, for the
hand-rolled version of exactly what this script does in one call).

Run with:
    uv run python examples/row_pivot_demo.py
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

# ---------------------------------------------------------------------------
# 2. Build the tree: every statistic is its own named, *raw* (unformatted)
#    value - row_pivot will combine/format them at table-build time, instead
#    of needing a pre-formatted "_mean_sd"-style helper inside analyze_by().
# ---------------------------------------------------------------------------
tree = (
    AnalysisTree()
    .split_by("df.AVISIT", label="Visit")
    .split_by("df.ARM", label="Arm")
    .analyze_by(
        n=lambda df: len(df),
        mean=lambda df: round(np.mean(df.AVAL), 1),
        sd=lambda df: round(np.std(df.AVAL, ddof=1), 1),
        median=lambda df: round(np.median(df.AVAL), 1),
        q1=lambda df: round(np.percentile(df.AVAL, 25), 1),
        q3=lambda df: round(np.percentile(df.AVAL, 75), 1),
        min=lambda df: round(np.min(df.AVAL), 1),
        max=lambda df: round(np.max(df.AVAL), 1),
    )
)
result = tree.run(df)

# ---------------------------------------------------------------------------
# 3. pivot_statistics=True: every statistic becomes its own COLUMN -
#    8 statistics x 2 arms = 16 data columns, one row per visit.
# ---------------------------------------------------------------------------
wide = simple_table(result, by="Arm", pivot_statistics=True)
print("=== pivot_statistics=True: every statistic becomes a column ===")
print(f"columns: {len(wide.columns)} -> {list(wide.columns)}")
print()

# ---------------------------------------------------------------------------
# 4. pivot_statistics=False (the default): every statistic already becomes
#    its own ROW - but each one stays separate, with its raw/unformatted
#    value and its literal statistic name as the row label. There's no way
#    to merge "mean" and "sd" into a single "46.2 (8.8)" row this way, and
#    no way to drop the statistics you don't want to display.
# ---------------------------------------------------------------------------
plain_rows = simple_table(result, by="Arm", pivot_statistics=False)
plain_rows = plain_rows.drop(columns=["_Level_0"]).rename(columns={"_Level_1": "Visit"})
print("=== pivot_statistics=False: every statistic becomes a row, unmerged ===")
print(plain_rows.head(8).to_string(index=False))
print("...")
print(
    f"total rows: {len(plain_rows)} (8 raw statistics x 4 visits, alphabetically ordered)"
)
print()

# ---------------------------------------------------------------------------
# 5. row_pivot: stacks a CHOSEN SUBSET of those statistics back into rows,
#    combining several raw statistics into one formatted cell per row, with
#    a custom label and order - the part pivot_statistics=False alone can't
#    do. Two ways to combine multiple statistics into one cell:
#      - a list of names, joined with ", "                 -> "n", "Min, Max"
#      - a callable, dispatched by parameter name like      -> "Mean (SD)",
#        analyze_by(), for full control over formatting        "Median (Q1, Q3)"
# ---------------------------------------------------------------------------
table = simple_table(
    result,
    by="Arm",
    pivot_statistics=True,
    row_pivot={
        "n": ["n"],
        "Mean (SD)": lambda mean, sd: f"{mean} ({sd})",
        "Median (Q1, Q3)": lambda median, q1, q3: f"{median} ({q1}, {q3})",
        "Min, Max": ["min", "max"],
    },
)
table = table.drop(columns=["_Level_0"]).rename(columns={"_Level_1": "Visit"})

print("=== row_pivot: a chosen subset of statistics are combined into rows ===")
print(table.to_string(index=False))

# ---------------------------------------------------------------------------
# 6. Great Tables (HTML) version of the row_pivot table, with the repeated
#    Visit label suppressed for the 3 extra rows per visit (already done by
#    simple_table's default suppress_duplicates=True).
# ---------------------------------------------------------------------------
gt = GT(table).tab_header(
    title="ALT (U/L) by Visit and Treatment Arm",
    subtitle="n; Mean (SD); Median (Q1, Q3); Min, Max - built with row_pivot",
)

out_path = "examples/out/row_pivot_demo.html"
with open(out_path, "w") as f:
    f.write(gt.as_raw_html())
print(f"\nSaved HTML table to {out_path}")

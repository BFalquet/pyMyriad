"""Classic clinical-trial lab table: value and change from baseline by visit and arm.

This is a refinement of lab_change_from_baseline_table.py that pushes more of the
work into the AnalysisTree itself, instead of pre/post-processing pandas DataFrames
around it:

- Change from baseline is computed *inside* the ``analyze_by`` lambda (point 4
  below), not as a precomputed ``Change`` column merged onto the whole dataset.
  AnalysisTree lambdas only ever see the current visit/arm subset of rows, so the
  one piece of outside information they need - each subject's baseline value - is
  supplied as a small captured lookup Series, not a full extra column.
- The lambdas return the final, presentation-ready strings directly (e.g.
  "46.2 (8.8)"), so there is no separate ``format_statistics`` pass afterward.
- ``split_by(..., label=...)`` already names the row/column hierarchy at
  construction time ("Visit", "Arm"); the analysis keys are written as their
  final display names too ("n", "Value, Mean (SD)", ...), so the only
  "renaming" left after pivoting is splitting the library's "Arm||Statistic"
  column names back apart - a structural consequence of the pivot, not a
  cosmetic fix-up.
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
# 2. The only thing the tree can't see on its own: each subject's baseline
#    value, looked up by USUBJID. This is metadata, not a derived data
#    column - it is captured by the analyze_by lambdas below rather than
#    merged onto every row of `df`.
# ---------------------------------------------------------------------------
baseline_lookup = df.loc[df.AVISIT == "Baseline"].set_index("USUBJID")["AVAL"]


def _mean_sd(x: pd.Series) -> str:
    return f"{np.mean(x):.1f} ({np.std(x, ddof=1):.1f})"


# ---------------------------------------------------------------------------
# 3-4. Build the analysis tree: rows = Visit, columns (pivoted later) = Arm.
#    Each statistic is computed - and, for "value"/"change", formatted - in
#    its own lambda. "Change from Baseline" is the per-subject difference
#    between this row's AVAL and that subject's own baseline value, computed
#    inline via `baseline_lookup`.
# ---------------------------------------------------------------------------
tree = (
    AnalysisTree()
    .split_by("df.AVISIT", label="Visit")
    .split_by("df.ARM", label="Arm")
    .analyze_by(
        **{
            "n": lambda df: len(df),
            "Value, Mean (SD)": lambda df: _mean_sd(df.AVAL),
            "Change from Baseline, Mean (SD)": lambda df: _mean_sd(
                df.AVAL - df.USUBJID.map(baseline_lookup)
            ),
        },
        label="Lab Summary",
    )
)
result = tree.run(df)

# ---------------------------------------------------------------------------
# 5. Pivot Arm to columns, each subdivided by statistic. Statistic names are
#    already final display names, so pivoting yields "Arm||Statistic"
#    columns directly - no separate relabeling step is needed, just an
#    explicit row/column order (pandas' pivot sorts both alphabetically,
#    which would scramble visit chronology and put "Change..." before "n").
# ---------------------------------------------------------------------------
table = simple_table(result, by="Arm", pivot_statistics=True)

visit_order = {v: i for i, v in enumerate(VISITS)}
table = (
    table.sort_values("_Level_1", key=lambda s: s.map(visit_order))
    .reset_index(drop=True)
    .drop(columns=["_Level_0"])
    .rename(columns={"_Level_1": "Visit"})
)
stat_order = ["n", "Value, Mean (SD)", "Change from Baseline, Mean (SD)"]
table = table[["Visit"] + [f"{arm}||{stat}" for arm in ARMS for stat in stat_order]]

print("=== ALT (U/L) by Visit and Treatment Arm ===")
print(table.to_string(index=False))

# ---------------------------------------------------------------------------
# 6. Great Tables (HTML) version with arm spanners over n / Value / Change.
#    Column labels come straight from the "Arm||Statistic" split - no
#    hand-written rename map.
# ---------------------------------------------------------------------------
arm_columns = {arm: [c for c in table.columns if c.startswith(f"{arm}||")] for arm in ARMS}

gt = GT(table).tab_header(
    title="ALT (U/L) by Visit and Treatment Arm",
    subtitle="Mean (SD); Change from Baseline = Visit value - Baseline value",
)
for arm, cols in arm_columns.items():
    gt = gt.tab_spanner(label=arm, columns=cols)
gt = gt.cols_label(**{c: c.split("||", 1)[1] for cols in arm_columns.values() for c in cols})
gt = gt.cols_align(align="center", columns=[c for cols in arm_columns.values() for c in cols])

out_path = "examples/out/lab_change_from_baseline_table_v2.html"
with open(out_path, "w") as f:
    f.write(gt.as_raw_html())
print(f"\nSaved HTML table to {out_path}")

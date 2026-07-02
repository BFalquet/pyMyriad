import numpy as np
import pandas as pd
import pytest

from pyMyriad.clinical import lab_summary_table


@pytest.fixture
def lab_df():
    """4 subjects x 2 visits x 2 arms, hand-computable statistics."""
    visits = pd.Categorical(
        ["Baseline", "Week 4"] * 4, categories=["Baseline", "Week 4"], ordered=True
    )
    arms = pd.Categorical(
        [
            "Placebo",
            "Placebo",
            "Placebo",
            "Placebo",
            "Active",
            "Active",
            "Active",
            "Active",
        ],
        categories=["Placebo", "Active"],
        ordered=True,
    )
    return pd.DataFrame(
        {
            "USUBJID": ["S1", "S1", "S2", "S2", "S3", "S3", "S4", "S4"],
            "AVISIT": visits,
            "ARM": arms,
            "AVAL": [10.0, 12.0, 20.0, 18.0, 30.0, 24.0, 40.0, 34.0],
        }
    )


def _call(df, **kwargs):
    kwargs.setdefault("baseline_level", "Baseline")
    return lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        **kwargs,
    )


def test_returns_dataframe_by_default(lab_df):
    """Regression test for #65: default call returns a DataFrame, not a GT."""
    table = _call(lab_df)
    assert isinstance(table, pd.DataFrame)


def test_row_shape_visit_x_statistic(lab_df):
    """2 visits x 4 default stats = 8 rows, in the documented stat order per visit."""
    table = _call(lab_df)
    assert len(table) == 8
    assert list(table.loc[table.Visit == "Baseline", "Statistic"]) == [
        "n",
        "Mean (SD)",
        "Median (Q1, Q3)",
        "Min, Max",
    ]


def test_column_shape_arm_x_value_change(lab_df):
    """Columns are Visit, Statistic, then Value/Change per arm in category order."""
    table = _call(lab_df)
    assert list(table.columns) == [
        "Visit",
        "Statistic",
        "Placebo||Value",
        "Placebo||Change",
        "Active||Value",
        "Active||Change",
    ]


def test_n_stat_value(lab_df):
    """Regression test for #65: n counts subjects per (visit, arm) group."""
    table = _call(lab_df)
    row = table[(table.Visit == "Week 4") & (table.Statistic == "n")].iloc[0]
    assert row["Placebo||Value"] == "2"
    assert row["Active||Value"] == "2"


def test_mean_sd_stat_value(lab_df):
    """Placebo Baseline values are [10, 20] -> mean 15.0, sd(ddof=1) ~= 7.1."""
    table = _call(lab_df)
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    expected = f"{np.mean([10, 20]):.1f} ({np.std([10, 20], ddof=1):.1f})"
    assert row["Placebo||Value"] == expected


def test_median_iqr_stat_value(lab_df):
    """Active Baseline values are [30, 40] -> hand-verified against np.percentile."""
    table = _call(lab_df)
    row = table[
        (table.Visit == "Baseline") & (table.Statistic == "Median (Q1, Q3)")
    ].iloc[0]
    q1, med, q3 = np.percentile([30, 40], [25, 50, 75])
    assert row["Active||Value"] == f"{med:.1f} ({q1:.1f}, {q3:.1f})"


def test_min_max_stat_value(lab_df):
    """Placebo Baseline values are [10, 20] -> Min, Max is '10.0, 20.0'."""
    table = _call(lab_df)
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Min, Max")].iloc[0]
    assert row["Placebo||Value"] == "10.0, 20.0"


def test_change_from_baseline_values(lab_df):
    """Regression test for #65: Change uses paired per-subject change, not group means.

    Placebo Week 4: S1 12-10=2, S2 18-20=-2 -> mean change 0.0.
    """
    table = _call(lab_df)
    row = table[(table.Visit == "Week 4") & (table.Statistic == "Mean (SD)")].iloc[0]
    expected = f"{np.mean([2, -2]):.1f} ({np.std([2, -2], ddof=1):.1f})"
    assert row["Placebo||Change"] == expected


def test_baseline_row_change_is_zero(lab_df):
    """Baseline rows have CHG == 0 for every subject (per change_from_baseline)."""
    table = _call(lab_df)
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["Placebo||Change"] == "0.0 (0.0)"
    assert row["Active||Change"] == "0.0 (0.0)"


def test_stats_subset_selection(lab_df):
    """Only the requested statistics appear as rows."""
    table = _call(lab_df, stats=("n", "mean_sd"))
    assert len(table) == 4
    assert set(table["Statistic"]) == {"n", "Mean (SD)"}


def test_stats_order_respected(lab_df):
    """Row order within each visit follows the `stats` tuple order."""
    table = _call(lab_df, stats=("min_max", "n"))
    assert list(table.loc[table.Visit == "Baseline", "Statistic"]) == [
        "Min, Max",
        "n",
    ]


def test_empty_stats_raises(lab_df):
    """Regression test for #65: empty `stats` is rejected up front."""
    with pytest.raises(ValueError):
        _call(lab_df, stats=())


def test_unknown_stat_raises(lab_df):
    """Regression test for #65: an invalid stat name raises with a clear message."""
    with pytest.raises(ValueError, match="mean"):
        _call(lab_df, stats=("mean",))


def test_visit_ordering_preserved_via_categorical():
    """Regression test for #65 (relies on #61): visit order follows categories, not alphabetical."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1", "S2", "S2"],
            "AVISIT": pd.Categorical(
                ["Week 4", "Baseline", "Week 4", "Baseline"],
                categories=["Week 4", "Baseline"],
                ordered=True,
            ),
            "ARM": ["A", "A", "A", "A"],
            "AVAL": [12.0, 10.0, 18.0, 20.0],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    assert list(pd.unique(table["Visit"])) == ["Week 4", "Baseline"]


def test_arm_ordering_preserved_via_categorical():
    """Regression test for #65 (relies on #61): arm column order follows categories."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1", "S2", "S2"],
            "AVISIT": ["Baseline", "Week 4", "Baseline", "Week 4"],
            "ARM": pd.Categorical(
                ["Active", "Active", "Placebo", "Placebo"],
                categories=["Active", "Placebo"],
                ordered=True,
            ),
            "AVAL": [10.0, 12.0, 20.0, 18.0],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    assert list(table.columns) == [
        "Visit",
        "Statistic",
        "Active||Value",
        "Active||Change",
        "Placebo||Value",
        "Placebo||Change",
    ]


def test_missing_baseline_level_raises(lab_df):
    """Regression test for #65: a nonexistent baseline_level fails fast."""
    with pytest.raises(ValueError):
        _call(lab_df, baseline_level="Nonexistent")


def test_change_col_collision_raises(lab_df):
    """Regression test for #65: an existing change_col column is never silently overwritten."""
    lab_df["_LAB_SUMMARY_CHG"] = 0
    with pytest.raises(KeyError):
        _call(lab_df)


def test_custom_change_col_name(lab_df):
    """A custom change_col is threaded through and produces the same result."""
    table = _call(lab_df, change_col="MY_CHG")
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["Placebo||Change"] == "0.0 (0.0)"


def test_nan_values_produce_na_string():
    """An entirely-missing (visit, arm) group renders 'NA' cells instead of crashing."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1"],
            "AVISIT": ["Baseline", "Week 4"],
            "ARM": ["A", "A"],
            "AVAL": [10.0, np.nan],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    row = table[(table.Visit == "Week 4") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["A||Value"] == "NA"


def test_single_subject_group_no_crash():
    """A single-subject group renders '(NA)' for sd instead of NaN/crashing."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1"],
            "AVISIT": ["Baseline", "Week 4"],
            "ARM": ["A", "A"],
            "AVAL": [10.0, 12.0],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    row = table[(table.Visit == "Baseline") & (table.Statistic == "Mean (SD)")].iloc[0]
    assert row["A||Value"] == "10.0 (NA)"


def test_single_arm_supported():
    """A DataFrame with only one arm level still builds a valid table."""
    df = pd.DataFrame(
        {
            "USUBJID": ["S1", "S1", "S2", "S2"],
            "AVISIT": ["Baseline", "Week 4", "Baseline", "Week 4"],
            "ARM": ["Placebo", "Placebo", "Placebo", "Placebo"],
            "AVAL": [10.0, 12.0, 20.0, 18.0],
        }
    )
    table = lab_summary_table(
        df,
        value_col="AVAL",
        visit_col="AVISIT",
        arm_col="ARM",
        subject_col="USUBJID",
        baseline_level="Baseline",
    )
    assert list(table.columns) == [
        "Visit",
        "Statistic",
        "Placebo||Value",
        "Placebo||Change",
    ]


def test_as_gt_returns_gt(lab_df):
    """Regression test for #65: as_gt=True returns a great_tables.GT instance."""
    from great_tables import GT

    result = _call(lab_df, as_gt=True)
    assert isinstance(result, GT)


def test_as_gt_title_subtitle(lab_df):
    """as_gt=True with a title builds without error."""
    from great_tables import GT

    result = _call(lab_df, as_gt=True, title="My Title")
    assert isinstance(result, GT)


def test_result_col_not_leaked_into_output(lab_df):
    """The internal change_col is never a literal column name in the returned table."""
    table = _call(lab_df)
    assert "_LAB_SUMMARY_CHG" not in table.columns

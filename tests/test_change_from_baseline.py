import warnings

import pandas as pd
import pytest

from pyMyriad import change_from_baseline


@pytest.fixture
def paired_df():
    return pd.DataFrame(
        {
            "ID": ["S1", "S1", "S1", "S2", "S2", "S2"],
            "VISIT": ["Baseline", "Week 4", "Week 8", "Baseline", "Week 4", "Week 8"],
            "VAL": [40.0, 42.0, 38.0, 50.0, 48.0, 45.0],
        }
    )


def test_basic_change_values(paired_df):
    """Regression test for #63: per-subject change is correctly computed."""
    out = change_from_baseline(
        paired_df,
        id_col="ID",
        value_col="VAL",
        baseline_level="Baseline",
        level_col="VISIT",
    )
    assert out.loc[(out.ID == "S1") & (out.VISIT == "Week 4"), "CHG"].iloc[0] == 2.0
    assert out.loc[(out.ID == "S1") & (out.VISIT == "Week 8"), "CHG"].iloc[0] == -2.0
    assert out.loc[(out.ID == "S2") & (out.VISIT == "Week 4"), "CHG"].iloc[0] == -2.0
    assert out.loc[(out.ID == "S2") & (out.VISIT == "Week 8"), "CHG"].iloc[0] == -5.0


def test_baseline_rows_have_zero_change(paired_df):
    """Baseline rows must have CHG == 0 (value minus itself)."""
    out = change_from_baseline(
        paired_df,
        id_col="ID",
        value_col="VAL",
        baseline_level="Baseline",
        level_col="VISIT",
    )
    baseline_rows = out[out.VISIT == "Baseline"]
    assert baseline_rows["CHG"].eq(0).all()


def test_returns_copy_not_inplace(paired_df):
    """Input DataFrame must not be modified."""
    _ = change_from_baseline(
        paired_df,
        id_col="ID",
        value_col="VAL",
        baseline_level="Baseline",
        level_col="VISIT",
    )
    assert "CHG" not in paired_df.columns


def test_result_col_rename(paired_df):
    """Custom result_col name is respected."""
    out = change_from_baseline(
        paired_df,
        id_col="ID",
        value_col="VAL",
        baseline_level="Baseline",
        level_col="VISIT",
        result_col="DELTA",
    )
    assert "DELTA" in out.columns
    assert "CHG" not in out.columns


def test_unmatched_subject_gets_nan():
    """A subject with no baseline row receives NaN, not an error."""
    df = pd.DataFrame(
        {
            "ID": ["S1", "S1", "S2"],
            "VISIT": ["Baseline", "Week 4", "Week 4"],
            "VAL": [40.0, 42.0, 30.0],
        }
    )
    out = change_from_baseline(
        df, id_col="ID", value_col="VAL", baseline_level="Baseline", level_col="VISIT"
    )
    # S2 has no baseline → NaN change
    assert pd.isna(out.loc[out.ID == "S2", "CHG"].iloc[0])
    # Row count is unchanged
    assert len(out) == len(df)


def test_warn_unmatched_emits_warning():
    """warn_unmatched=True emits a UserWarning when subjects lack a baseline."""
    df = pd.DataFrame(
        {
            "ID": ["S1", "S2"],
            "VISIT": ["Week 4", "Week 4"],
            "VAL": [42.0, 30.0],
        }
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        change_from_baseline(
            df,
            id_col="ID",
            value_col="VAL",
            baseline_level="Baseline",
            level_col="VISIT",
            warn_unmatched=True,
        )
    assert len(caught) == 1
    assert issubclass(caught[0].category, UserWarning)
    assert "2 subject(s)" in str(caught[0].message)


def test_no_warning_when_all_matched(paired_df):
    """warn_unmatched=True stays silent when every subject has a baseline."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        change_from_baseline(
            paired_df,
            id_col="ID",
            value_col="VAL",
            baseline_level="Baseline",
            level_col="VISIT",
            warn_unmatched=True,
        )
    assert len(caught) == 0


def test_warn_unmatched_false_by_default():
    """No warning is emitted by default even when subjects are unmatched."""
    df = pd.DataFrame({"ID": ["S1"], "VISIT": ["Week 4"], "VAL": [42.0]})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        change_from_baseline(
            df,
            id_col="ID",
            value_col="VAL",
            baseline_level="Baseline",
            level_col="VISIT",
        )
    assert len(caught) == 0


def test_integer_id_col():
    """Integer subject IDs work identically to string IDs."""
    df = pd.DataFrame(
        {
            "ID": [1, 1, 2, 2],
            "VISIT": ["Baseline", "Week 4", "Baseline", "Week 4"],
            "VAL": [10.0, 12.0, 20.0, 18.0],
        }
    )
    out = change_from_baseline(
        df, id_col="ID", value_col="VAL", baseline_level="Baseline", level_col="VISIT"
    )
    assert out.loc[(out.ID == 1) & (out.VISIT == "Week 4"), "CHG"].iloc[0] == 2.0
    assert out.loc[(out.ID == 2) & (out.VISIT == "Week 4"), "CHG"].iloc[0] == -2.0


def test_integration_with_analysis_tree(paired_df):
    """Regression test for #63: CHG column is usable inside analyze_by lambdas."""
    from pyMyriad import AnalysisTree, simple_table

    df = change_from_baseline(
        paired_df,
        id_col="ID",
        value_col="VAL",
        baseline_level="Baseline",
        level_col="VISIT",
    )
    tree = (
        AnalysisTree()
        .split_by("df.VISIT", label="Visit")
        .analyze_by(
            n=lambda df: df["CHG"].notna().sum(),
            mean_chg=lambda df: round(df["CHG"].mean(), 1),
        )
    )
    result = tree.run(df)
    table = simple_table(result, by="Visit")

    # Baseline column should show CHG == 0 for all subjects
    assert table.loc[table.Statistic == "mean_chg", "Baseline"].iloc[0] == 0.0
    # Week 4 mean change: S1 +2, S2 -2 → mean = 0
    assert table.loc[table.Statistic == "mean_chg", "Week 4"].iloc[0] == 0.0
    # Week 8 mean change: S1 -2, S2 -5 → mean = -3.5
    assert table.loc[table.Statistic == "mean_chg", "Week 8"].iloc[0] == -3.5

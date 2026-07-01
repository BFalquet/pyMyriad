import pytest
import pandas as pd
import numpy as np
from pyMyriad import AnalysisTree, simple_table, cascade_table
from pyMyriad.listing import _clean_path_element, _split_path_into_levels


def test_clean_path_element():
    """Test path element cleaning."""
    assert _clean_path_element("df.Gender") == "Gender"
    assert _clean_path_element("Gender") == "Gender"
    assert _clean_path_element(None) == ""
    assert _clean_path_element("df.Age > 40") == "Age > 40"


def test_split_path_into_levels():
    """Test splitting paths into hierarchical levels."""
    df = pd.DataFrame(
        {
            "path": [
                ["root", "df.Gender", "M", "analysis"],
                ["root", "df.Gender", "F", "df.Country", "US", "analysis"],
            ],
            "value": [1, 2],
        }
    )

    result, level_cols = _split_path_into_levels(df, path_col="path")

    assert "_Level_0" in result.columns
    assert "_Level_1" in result.columns
    assert "_Level_2" in result.columns
    assert result.loc[0, "_Level_0"] == "Gender"
    assert result.loc[0, "_Level_1"] == "M"
    assert result.loc[1, "_Level_0"] == "Gender"
    assert result.loc[1, "_Level_1"] == "F"
    assert result.loc[1, "_Level_2"] == "Country"
    assert level_cols == ["_Level_0", "_Level_1", "_Level_2", "_Level_3"]


def test_simple_table_basic():
    """Test simple_table with basic hierarchical analysis."""
    df = pd.DataFrame(
        {
            "Gender": ["M", "M", "F", "F", "M", "F"],
            "Country": ["US", "UK", "US", "UK", "US", "UK"],
            "Age": [25, 35, 45, 55, 30, 40],
            "Income": [50000, 60000, 70000, 80000, 55000, 75000],
        }
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(mean_income=lambda df: np.mean(df.Income), count=lambda df: len(df))
    )

    dtree = atree.run(df)
    result = simple_table(dtree)

    # Check that we have the expected columns
    assert "_Level_0" in result.columns
    assert "_Level_1" in result.columns
    assert "_Level_2" in result.columns
    assert "Statistic" in result.columns
    assert "Value" in result.columns

    # Analysis column should not be present by default
    assert "Analysis" not in result.columns

    # Check that we have the right number of rows (4 groups * 2 statistics)
    assert len(result) == 8

    # Check that paths are properly split
    assert "Gender" in result["_Level_0"].values
    assert "M" in result["_Level_1"].values
    assert "F" in result["_Level_1"].values
    assert "Country" in result["_Level_2"].values


def test_simple_table_with_pivot():
    """Test simple_table with pivot functionality."""
    df = pd.DataFrame(
        {
            "Gender": ["M", "M", "F", "F", "M", "F"],
            "Country": ["US", "UK", "US", "UK", "US", "UK"],
            "Income": [50000, 60000, 70000, 80000, 55000, 75000],
        }
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree = atree.run(df)
    result = simple_table(dtree, by="df.Gender")

    # Check that we have pivoted values (F and M columns)
    assert "F" in result.columns
    assert "M" in result.columns

    # Check that we have the right structure (columns use underscore prefix)
    assert "_Level_0" in result.columns  # Should still have Country label
    assert "_Level_1" in result.columns  # Should have Country values

    # Check that rows are properly combined (not duplicated)
    # Should have 2 countries * 1 statistic = 2 rows
    assert len(result) == 2


def test_simple_table_single_level():
    """Test simple_table with single level analysis."""
    df = pd.DataFrame(
        {"Gender": ["M", "M", "F", "F"], "Income": [50000, 60000, 70000, 80000]}
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .analyze_by(
            mean_income=lambda df: np.mean(df.Income),
            std_income=lambda df: np.std(df.Income),
        )
    )

    dtree = atree.run(df)
    result = simple_table(dtree)

    # Check basic structure
    assert "_Level_0" in result.columns
    assert "_Level_1" in result.columns
    assert "Statistic" in result.columns
    assert "Value" in result.columns

    # Analysis column should not be present by default
    assert "Analysis" not in result.columns

    # Should have 2 groups * 2 statistics = 4 rows
    assert len(result) == 4


def test_simple_table_no_split():
    """Test simple_table with analysis but no splits."""
    df = pd.DataFrame({"Income": [50000, 60000, 70000, 80000]})

    atree = AnalysisTree().analyze_by(
        mean_income=lambda df: np.mean(df.Income), count=lambda df: len(df)
    )

    dtree = atree.run(df)
    result = simple_table(dtree)

    # Should still have analysis results
    assert "Statistic" in result.columns
    assert "Value" in result.columns

    # Analysis column should not be present by default
    assert "Analysis" not in result.columns

    assert len(result) == 2  # 2 statistics


def test_cascade_table():
    """Test cascade_table includes all tree nodes."""
    df = pd.DataFrame(
        {"Gender": ["M", "M", "F", "F"], "Income": [50000, 60000, 70000, 80000]}
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree = atree.run(df)

    # simple_table shows only analysis rows
    result_analysis_only = simple_table(dtree)

    # cascade_table shows all tree nodes
    result_all = cascade_table(dtree)

    # cascade_table should have more rows than simple_table
    assert len(result_all) >= len(result_analysis_only)


def test_cascade_table_with_pivot():
    """Test cascade_table with by parameter for pivoting."""
    df = pd.DataFrame(
        {
            "Gender": ["M", "M", "F", "F", "M", "F"],
            "Country": ["US", "UK", "US", "UK", "US", "UK"],
            "Income": [50000, 60000, 70000, 80000, 55000, 75000],
        }
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree = atree.run(df)

    # cascade_table with by should work without errors
    result = cascade_table(dtree, by="df.Gender")

    # Should have pivot columns (F and M)
    assert "F" in result.columns
    assert "M" in result.columns

    # Should have more rows than simple_table due to hierarchy markers
    simple_result = simple_table(dtree, by="df.Gender")
    assert len(result) >= len(simple_result)

    # Test with pivot_statistics as well
    result_pivot = cascade_table(dtree, by="df.Gender", pivot_statistics=True)
    assert len(result_pivot) > 0


def test_simple_table_no_split_path():
    """Test simple_table with split_path=False."""
    df = pd.DataFrame(
        {"Gender": ["M", "M", "F", "F"], "Income": [50000, 60000, 70000, 80000]}
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree = atree.run(df)
    result = simple_table(dtree, split_path=False)

    # Should not have _Level_* columns
    level_cols = [c for c in result.columns if c.startswith("_Level_")]
    assert len(level_cols) == 0


def test_simple_table_empty_result():
    """Test simple_table with empty analysis tree."""
    df = pd.DataFrame(
        {"Gender": ["M", "M", "F", "F"], "Income": [50000, 60000, 70000, 80000]}
    )

    # Create a tree with only splits, no analysis
    atree = AnalysisTree().split_by("df.Gender")

    dtree = atree.run(df)
    result = simple_table(dtree)

    # Should return a message about no results
    assert "Message" in result.columns or len(result) == 0


def test_simple_table_multiple_analyses():
    """Test simple_table with multiple analysis nodes at different levels."""
    df = pd.DataFrame(
        {
            "Gender": ["M", "M", "F", "F", "M", "F"],
            "Country": ["US", "UK", "US", "UK", "US", "UK"],
            "Income": [50000, 60000, 70000, 80000, 55000, 75000],
            "Age": [25, 35, 45, 55, 30, 40],
        }
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .summarize_by(gender_mean=lambda df: np.mean(df.Income))
        .split_by("df.Country")
        .analyze_by(
            country_mean=lambda df: np.mean(df.Income),
            age_mean=lambda df: np.mean(df.Age),
        )
    )

    dtree = atree.run(df)

    # Without include_label, Analysis column should not be present
    result = simple_table(dtree)
    assert len(result) > 0
    assert "Analysis" not in result.columns

    # With include_label=True, Analysis column should be present
    result_with_label = simple_table(dtree, include_label=True)
    assert "Analysis" in result_with_label.columns

    # Check that we have different analysis labels
    analysis_labels = result_with_label["Analysis"].unique()
    assert len(analysis_labels) > 0


def test_analysis_column_removed():
    """Test that the Analysis column is removed from output."""
    df = pd.DataFrame(
        {"Gender": ["M", "M", "F", "F"], "Income": [50000, 60000, 70000, 80000]}
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree = atree.run(df)
    result = simple_table(dtree)

    # Analysis column should not be present
    assert "Analysis" not in result.columns


def test_duplicate_suppression():
    """Test that consecutive duplicate values are suppressed."""
    df = pd.DataFrame(
        {
            "Gender": ["M", "M", "F", "F"],
            "Country": ["US", "UK", "US", "UK"],
            "Income": [50000, 60000, 70000, 80000],
        }
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(mean_income=lambda df: np.mean(df.Income), count=lambda df: len(df))
    )

    dtree = atree.run(df)
    result = simple_table(dtree, suppress_duplicates=True)

    # Check that duplicates are suppressed (empty strings)
    # First row should have Gender value
    assert result.iloc[0]["_Level_0"] == "Gender"
    assert result.iloc[0]["_Level_1"] == "F"

    # Second row (same Gender, same Level_1) should have empty strings
    assert result.iloc[1]["_Level_0"] == ""
    assert result.iloc[1]["_Level_1"] == ""

    # When Level_1 changes, it should show again
    assert result.iloc[4]["_Level_1"] == "M"


def test_no_duplicate_suppression():
    """Test that duplicate suppression can be disabled."""
    df = pd.DataFrame(
        {
            "Gender": ["M", "M", "F", "F"],
            "Country": ["US", "UK", "US", "UK"],
            "Income": [50000, 60000, 70000, 80000],
        }
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree = atree.run(df)
    result = simple_table(dtree, suppress_duplicates=False)

    # All rows should have values (no empty strings)
    assert all(result["_Level_0"] == "Gender")
    assert "F" in result["_Level_1"].values
    assert "M" in result["_Level_1"].values


def test_pivot_removes_correct_level():
    """Test that pivoting removes the correct level column."""
    df = pd.DataFrame(
        {
            "Gender": ["M", "M", "F", "F"],
            "Country": ["US", "UK", "US", "UK"],
            "Age": [25, 35, 45, 55],
            "Income": [50000, 60000, 70000, 80000],
        }
    )

    # Test pivoting by Gender (first split)
    atree1 = (
        AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree1 = atree1.run(df)
    result1 = simple_table(dtree1, by="df.Gender")

    # And pivot columns should exist
    assert "F" in result1.columns
    assert "M" in result1.columns

    # Check _Level columns exist (with underscore prefix)
    level_cols = [c for c in result1.columns if c.startswith("_Level_")]
    assert len(level_cols) > 0

    # Test pivoting by Country (second split)
    atree2 = (
        AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree2 = atree2.run(df)
    result2 = simple_table(dtree2, by="df.Country")

    # And pivot columns should exist
    assert "US" in result2.columns
    assert "UK" in result2.columns

    # Check _Level columns exist (with underscore prefix)
    level_cols = [c for c in result2.columns if c.startswith("_Level_")]
    assert len(level_cols) > 0


def test_pivot_combines_rows():
    """Test that pivoting properly combines rows instead of duplicating."""
    df = pd.DataFrame(
        {
            "Gender": ["M", "M", "F", "F"],
            "Country": ["US", "UK", "US", "UK"],
            "Income": [50000, 60000, 70000, 80000],
        }
    )

    atree = (
        AnalysisTree()
        .split_by("df.Gender")
        .split_by("df.Country")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )

    dtree = atree.run(df)
    result = simple_table(dtree, by="df.Gender")

    # Should have 2 rows (one for each country), not 4
    assert len(result) == 2

    # Each row should have both F and M values
    for idx in range(len(result)):
        row = result.iloc[idx]
        # At least one of F or M should have a value
        assert pd.notna(row["F"]) or pd.notna(row["M"])


def test_helper_clean_path_element():
    """Test the _clean_path_element helper function."""
    from pyMyriad.listing import _clean_path_element

    assert _clean_path_element("df.Gender") == "Gender"
    assert _clean_path_element("Gender") == "Gender"
    assert _clean_path_element("df.Age > 40") == "Age > 40"
    assert _clean_path_element(None) == ""


def test_helper_suppress_duplicates():
    """Test the _suppress_duplicate_values helper function."""
    from pyMyriad.listing import _suppress_duplicate_values

    df = pd.DataFrame({"A": ["x", "x", "y", "y", "y"], "B": [1, 2, 3, 4, 5]})

    result = _suppress_duplicate_values(df, ["A"])

    # First occurrence should remain
    assert result.iloc[0]["A"] == "x"
    # Second occurrence should be suppressed
    assert result.iloc[1]["A"] == ""
    # New value should appear
    assert result.iloc[2]["A"] == "y"
    # Subsequent occurrences should be suppressed
    assert result.iloc[3]["A"] == ""
    assert result.iloc[4]["A"] == ""
    # Column B should be unchanged
    assert list(result["B"]) == [1, 2, 3, 4, 5]


def test_simple_table_by_does_not_substring_match_split_label():
    """Regression test for #59: by= must match a split's label exactly.

    A split labeled "Arm" must not accidentally pivot (or fail to pivot)
    based on whether the requested `by` string happens to contain "Arm" as
    a substring of something else - it must match the label exactly, and
    raise a clear error when there is no match.
    """
    df = pd.DataFrame(
        {
            "ARM": ["Placebo", "Active", "Placebo", "Active"],
            "Outcome": [1, 2, 3, 4],
        }
    )
    atree = (
        AnalysisTree()
        .split_by("df.ARM", label="Arm")
        .analyze_by(mean=lambda df: np.mean(df.Outcome))
    )
    dtree = atree.run(df)

    # Exact label match pivots correctly.
    result = simple_table(dtree, by="Arm")
    assert "Placebo" in result.columns
    assert "Active" in result.columns

    # A by= value that happens to contain the label as a substring (or vice
    # versa) must not silently match - it should raise instead of silently
    # returning an unpivoted table.
    with pytest.raises(ValueError, match="Arm"):
        simple_table(dtree, by="df.ARM")

    with pytest.raises(ValueError, match="Arm"):
        cascade_table(dtree, by="df.ARM")


def test_simple_table_pivot_columns_preserve_categorical_order():
    """Regression test for #61: pivoted columns follow category order, not alphabetical.

    "Week 12" sorts before "Week 4" and "Week 8" alphabetically, so a plain
    string sort would scramble visit chronology. The split column's ordered
    Categorical dtype should be respected instead.
    """
    df = pd.DataFrame(
        {
            "AVISIT": pd.Categorical(
                ["Week 4", "Baseline", "Week 12", "Week 8"] * 5,
                categories=["Baseline", "Week 4", "Week 8", "Week 12"],
                ordered=True,
            ),
            "Val": np.arange(20.0),
        }
    )
    atree = (
        AnalysisTree().split_by("df.AVISIT").analyze_by(mean=lambda df: np.mean(df.Val))
    )
    dtree = atree.run(df)

    result = simple_table(dtree, by="df.AVISIT")
    assert list(result.columns) == [
        "Statistic",
        "Baseline",
        "Week 4",
        "Week 8",
        "Week 12",
    ]


def test_simple_table_pivot_statistics_columns_preserve_categorical_order():
    """Regression test for #61: same ordering guarantee with pivot_statistics=True."""
    df = pd.DataFrame(
        {
            "AVISIT": pd.Categorical(
                ["Week 4", "Baseline", "Week 12", "Week 8"] * 5,
                categories=["Baseline", "Week 4", "Week 8", "Week 12"],
                ordered=True,
            ),
            "Val": np.arange(20.0),
        }
    )
    atree = (
        AnalysisTree().split_by("df.AVISIT").analyze_by(mean=lambda df: np.mean(df.Val))
    )
    dtree = atree.run(df)

    result = simple_table(dtree, by="df.AVISIT", pivot_statistics=True)
    assert list(result.columns) == [
        "Baseline||mean",
        "Week 4||mean",
        "Week 8||mean",
        "Week 12||mean",
    ]


def test_cascade_table_pivot_columns_preserve_categorical_order():
    """Regression test for #61: cascade_table column order also follows category order."""
    df = pd.DataFrame(
        {
            "AVISIT": pd.Categorical(
                ["Week 4", "Baseline", "Week 12", "Week 8"] * 5,
                categories=["Baseline", "Week 4", "Week 8", "Week 12"],
                ordered=True,
            ),
            "Val": np.arange(20.0),
        }
    )
    atree = (
        AnalysisTree().split_by("df.AVISIT").analyze_by(mean=lambda df: np.mean(df.Val))
    )
    dtree = atree.run(df)

    result = cascade_table(dtree, by="df.AVISIT")
    pivoted_cols = [c for c in result.columns if c not in ("_Level_0", "statistics")]
    assert pivoted_cols == ["Baseline", "Week 4", "Week 8", "Week 12"]

    result_stats = cascade_table(dtree, by="df.AVISIT", pivot_statistics=True)
    assert list(result_stats.columns) == [
        "Baseline||mean",
        "Week 4||mean",
        "Week 8||mean",
        "Week 12||mean",
    ]


def test_simple_table_row_order_preserves_categorical_order_for_unpivoted_split():
    """Regression test for #61: a non-pivoted categorical split keeps its row order.

    Mirrors the real-world pattern in examples/lab_change_from_baseline_table_v2.py:
    Visit is split first (and not pivoted), Arm is split second and pivoted -
    the Visit row order used to require a hand-written sort_values(key=...).
    """
    df = pd.DataFrame(
        {
            "AVISIT": pd.Categorical(
                ["Week 4", "Baseline", "Week 12", "Week 8"] * 5,
                categories=["Baseline", "Week 4", "Week 8", "Week 12"],
                ordered=True,
            ),
            "ARM": ["A", "B"] * 10,
            "Val": np.arange(20.0),
        }
    )
    atree = (
        AnalysisTree()
        .split_by("df.AVISIT", label="Visit")
        .split_by("df.ARM", label="Arm")
        .analyze_by(mean=lambda df: np.mean(df.Val))
    )
    dtree = atree.run(df)

    result = simple_table(dtree, by="Arm")
    visits = result["_Level_1"].tolist()
    assert visits == ["Baseline", "Week 4", "Week 8", "Week 12"]


def test_simple_table_non_categorical_split_remains_alphabetical():
    """Non-categorical splits have no inherent order, so alphabetical stays the default."""
    df = pd.DataFrame(
        {"Group": ["Zebra", "Apple", "Mango"] * 5, "Val": np.arange(15.0)}
    )
    atree = (
        AnalysisTree().split_by("df.Group").analyze_by(mean=lambda df: np.mean(df.Val))
    )
    dtree = atree.run(df)

    result = simple_table(dtree, by="df.Group")
    assert list(result.columns) == ["Statistic", "Apple", "Mango", "Zebra"]


def test_simple_table_by_analysis_produces_label_pivot_columns():
    """Regression test for #70: by='Analysis' turns analyze_by() labels into columns."""
    df = pd.DataFrame({"G": ["M", "M", "F", "F"], "V": [1.0, 2.0, 3.0, 4.0]})
    atree = (
        AnalysisTree()
        .split_by("df.G", label="Group")
        .analyze_by(n=lambda df: len(df), label="Raw")
        .analyze_by(n=lambda df: len(df) * 10, label="Scaled")
    )
    dtree = atree.run(df)
    result = simple_table(dtree, by="Analysis")

    assert "Raw" in result.columns
    assert "Scaled" in result.columns
    assert "Statistic" in result.columns


def test_simple_table_by_split_and_analysis_produces_composite_columns():
    """Regression test for #70: by=['Split','Analysis'] gives '{Split} > {Label}' columns."""
    df = pd.DataFrame({"G": ["M", "M", "F", "F"], "V": [1.0, 2.0, 3.0, 4.0]})
    atree = (
        AnalysisTree()
        .split_by("df.G", label="Group")
        .analyze_by(n=lambda df: len(df), label="Raw")
        .analyze_by(n=lambda df: len(df) * 10, label="Scaled")
    )
    dtree = atree.run(df)
    result = simple_table(dtree, by=["Group", "Analysis"])

    assert "F > Raw" in result.columns
    assert "F > Scaled" in result.columns
    assert "M > Raw" in result.columns
    assert "M > Scaled" in result.columns


def test_simple_table_by_split_and_analysis_merges_label_rows():
    """Regression test for #70: Raw and Scaled values appear on the same output row."""
    df = pd.DataFrame({"G": ["M", "M", "F", "F"], "V": [1.0, 2.0, 3.0, 4.0]})
    atree = (
        AnalysisTree()
        .split_by("df.G", label="Group")
        .analyze_by(n=lambda df: len(df), label="Raw")
        .analyze_by(n=lambda df: len(df) * 10, label="Scaled")
    )
    dtree = atree.run(df)
    result = simple_table(dtree, by=["Group", "Analysis"])

    n_row = result[result["Statistic"] == "n"]
    assert len(n_row) == 1
    assert n_row["F > Raw"].iloc[0] == 2
    assert n_row["F > Scaled"].iloc[0] == 20
    assert n_row["M > Raw"].iloc[0] == 2
    assert n_row["M > Scaled"].iloc[0] == 20


def test_simple_table_by_analysis_clinical_table_shape():
    """Regression test for #70: full change-from-baseline table structure."""
    df = pd.DataFrame(
        {
            "Visit": pd.Categorical(
                ["Baseline", "Week 4"] * 6,
                categories=["Baseline", "Week 4"],
                ordered=True,
            ),
            "ARM": pd.Categorical(
                (["A"] * 3 + ["B"] * 3) * 2, categories=["A", "B"], ordered=True
            ),
            "AVAL": np.arange(12.0),
        }
    )
    df["CHG"] = df["AVAL"] - df.groupby("ARM", observed=True)["AVAL"].transform("first")

    tree = (
        AnalysisTree()
        .split_by("df.Visit", label="Visit")
        .split_by("df.ARM", label="Arm")
        .analyze_by(
            n=lambda df: len(df),
            mean=lambda df: round(np.mean(df.AVAL), 1),
            label="Value",
        )
        .analyze_by(
            n=lambda df: len(df),
            mean=lambda df: round(np.mean(df.CHG), 1),
            label="Change",
        )
    )
    result = tree.run(df)
    table = simple_table(result, by=["Arm", "Analysis"])

    assert list(table.columns) == [
        "_Level_0",
        "_Level_1",
        "Statistic",
        "A > Value",
        "A > Change",
        "B > Value",
        "B > Change",
    ]
    # Each statistic on exactly one row per visit — no duplicate rows.
    assert len(table) == 4  # 2 visits × 2 statistics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

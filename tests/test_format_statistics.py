from pyMyriad import *
import pytest

def test_format_statistics_global():
    """Test global format specification."""
    dtree = DataTree(
        a = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3})
    )
    
    result = format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="result", inplace=True)
    
    assert result is dtree  # Should return same object when inplace=True
    assert "result" in dtree["a"].summary
    assert dtree["a"].summary["result"] == "10.5 +/- 2.3"
    # Original statistics should still be there
    assert dtree["a"].summary["m"] == 10.5
    assert dtree["a"].summary["sd"] == 2.3


def test_format_statistics_per_label():
    """Test format specification per label."""
    dtree = DataTree(
        mean_node = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}),
        median_node = DataNode(label="Median", summary={"median": 11, "q1": 9, "q3": 13})
    )
    
    format_statistics(
        dtree, 
        format_map={"Mean": "{m} +/- {sd}", "Median": "{median} [{q1}-{q3}]"},
        stat_name="summary_text",
        inplace=True
    )
    
    assert dtree["mean_node"].summary["summary_text"] == "10.5 +/- 2.3"
    assert dtree["median_node"].summary["summary_text"] == "11 [9-13]"


def test_format_statistics_nested():
    """Test formatting in nested tree structure."""
    dtree = DataTree(
        s = SplitDataNode(
            split_var="VAR",
            lvl1=LvlDataNode(
                split_lvl="Level1",
                group1=DataNode(
                    label="Group 1",
                    summary={"mean": 10.2, "sd": 1.5}
                ),
                group2=DataNode(
                    label="Group 2",
                    summary={"mean": 20.8, "sd": 3.2}
                )
            )
        )
    )
    
    format_statistics(dtree, format_spec="{mean} ± {sd}", stat_name="formatted", inplace=True)
    
    assert dtree["s"]["lvl1"]["group1"].summary["formatted"] == "10.2 ± 1.5"
    assert dtree["s"]["lvl1"]["group2"].summary["formatted"] == "20.8 ± 3.2"


def test_format_statistics_no_format_error():
    """Test that error is raised when no format is provided."""
    dtree = DataTree(
        a = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3})
    )
    
    with pytest.raises(ValueError, match="Either format_spec or format_map must be provided"):
        format_statistics(dtree)


def test_format_statistics_missing_stat_error():
    """Test that error is raised when format references non-existent statistic."""
    dtree = DataTree(
        a = DataNode(label="Mean", summary={"m": 10.5})
    )
    
    with pytest.raises(KeyError, match="non-existent statistic"):
        format_statistics(dtree, format_spec="{m} +/- {sd}", inplace=True)


def test_format_statistics_numeric_formatting():
    """Test numeric formatting options."""
    dtree = DataTree(
        a = DataNode(label="Mean", summary={"m": 10.523456, "sd": 2.3789})
    )
    
    format_statistics(dtree, format_spec="{m:.2f} +/- {sd:.2f}", stat_name="rounded", inplace=True)
    
    assert dtree["a"].summary["rounded"] == "10.52 +/- 2.38"


def test_format_statistics_mixed_label_and_global():
    """Test that label-specific format overrides global format."""
    dtree = DataTree(
        node1 = DataNode(label="Special", summary={"m": 10.5, "sd": 2.3}),
        node2 = DataNode(label="Normal", summary={"m": 15.2, "sd": 1.8})
    )
    
    format_statistics(
        dtree,
        format_spec="{m} +/- {sd}",  # Global default
        format_map={"Special": "{m} (SD={sd})"},  # Override for "Special"
        stat_name="text",
        inplace=True
    )
    
    assert dtree["node1"].summary["text"] == "10.5 (SD=2.3)"
    assert dtree["node2"].summary["text"] == "15.2 +/- 1.8"


def test_format_statistics_no_summary():
    """Test that nodes without summary are handled gracefully."""
    dtree = DataTree(
        a = DataNode(label="NoStats", summary=None),
        b = DataNode(label="WithStats", summary={"m": 10.5, "sd": 2.3})
    )
    
    format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="result", inplace=True)
    
    # Node with no summary should be unchanged
    assert dtree["a"].summary is None
    # Node with summary should be formatted
    assert dtree["b"].summary["result"] == "10.5 +/- 2.3"


def test_format_statistics_inplace_false():
    """Test that inplace=False creates a copy and leaves original unchanged."""
    dtree = DataTree(
        a = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3})
    )
    
    original_summary = dtree["a"].summary.copy()
    
    # Format with inplace=False (default)
    new_dtree = format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="result")
    
    # Original should be unchanged
    assert dtree["a"].summary == original_summary
    assert "result" not in dtree["a"].summary
    
    # New tree should have the formatted result
    assert new_dtree is not dtree  # Should be a different object
    assert "result" in new_dtree["a"].summary
    assert new_dtree["a"].summary["result"] == "10.5 +/- 2.3"
    assert new_dtree["a"].summary["m"] == 10.5
    assert new_dtree["a"].summary["sd"] == 2.3


def test_format_statistics_inplace_true():
    """Test that inplace=True modifies the original tree."""
    dtree = DataTree(
        a = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3})
    )
    
    # Format with inplace=True
    result = format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="result", inplace=True)
    
    # Should return the same object
    assert result is dtree
    
    # Original should be modified
    assert "result" in dtree["a"].summary
    assert dtree["a"].summary["result"] == "10.5 +/- 2.3"


def test_format_statistics_remove_original():
    """Test that original statistics are removed when remove_original=True."""
    dtree = DataTree(
        a = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3, "n": 100})
    )
    
    format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="result", remove_original=True, inplace=True)
    
    # Original statistics used in format should be removed
    assert "m" not in dtree["a"].summary
    assert "sd" not in dtree["a"].summary
    # Statistics not used in format should be preserved
    assert dtree["a"].summary["n"] == 100
    # Formatted result should be present
    assert dtree["a"].summary["result"] == "10.5 +/- 2.3"


def test_format_statistics_remove_original_with_format_spec():
    """Test that only statistics used in format string are removed."""
    dtree = DataTree(
        a = DataNode(label="Stats", summary={"mean": 45.2, "sd": 8.7, "median": 44.5, "n": 150})
    )
    
    format_statistics(dtree, format_spec="{mean:.1f} ± {sd:.1f}", stat_name="formatted", remove_original=True, inplace=True)
    
    # Used statistics should be removed
    assert "mean" not in dtree["a"].summary
    assert "sd" not in dtree["a"].summary
    # Unused statistics should be preserved
    assert dtree["a"].summary["median"] == 44.5
    assert dtree["a"].summary["n"] == 150
    # Formatted result should be present
    assert dtree["a"].summary["formatted"] == "45.2 ± 8.7"


def test_format_statistics_multiple_rounds():
    """Test multiple rounds of formatting."""
    dtree = DataTree(
        a = DataNode(label="Data", summary={"m": 10.5, "sd": 2.3, "ci_lower": 9.8, "ci_upper": 11.2})
    )
    
    # First round: create mean_sd
    format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="mean_sd", inplace=True)
    assert dtree["a"].summary["mean_sd"] == "10.5 +/- 2.3"
    
    # Second round: create ci_range
    format_statistics(dtree, format_spec="({ci_lower}, {ci_upper})", stat_name="ci_range", inplace=True)
    assert dtree["a"].summary["ci_range"] == "(9.8, 11.2)"
    
    # Third round: combine both
    format_statistics(dtree, format_spec="{mean_sd}, CI: {ci_range}", stat_name="full", inplace=True)
    assert dtree["a"].summary["full"] == "10.5 +/- 2.3, CI: (9.8, 11.2)"
    
    # All intermediate statistics should still be present
    assert "m" in dtree["a"].summary
    assert "sd" in dtree["a"].summary
    assert "ci_lower" in dtree["a"].summary
    assert "ci_upper" in dtree["a"].summary


def test_format_statistics_multiple_rounds_with_removal():
    """Test multiple rounds of formatting with removal of intermediates."""
    dtree = DataTree(
        a = DataNode(label="Data", summary={"m": 10.5, "sd": 2.3, "ci_lower": 9.8, "ci_upper": 11.2, "n": 100})
    )
    
    # First round: create mean_sd, remove originals
    format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="mean_sd", remove_original=True, inplace=True)
    assert "m" not in dtree["a"].summary
    assert "sd" not in dtree["a"].summary
    assert dtree["a"].summary["mean_sd"] == "10.5 +/- 2.3"
    
    # Second round: create ci_range, remove originals
    format_statistics(dtree, format_spec="({ci_lower}, {ci_upper})", stat_name="ci_range", remove_original=True, inplace=True)
    assert "ci_lower" not in dtree["a"].summary
    assert "ci_upper" not in dtree["a"].summary
    assert dtree["a"].summary["ci_range"] == "(9.8, 11.2)"
    
    # Third round: combine both, remove intermediates
    format_statistics(dtree, format_spec="{mean_sd}, CI: {ci_range}", stat_name="full", remove_original=True, inplace=True)
    assert "mean_sd" not in dtree["a"].summary
    assert "ci_range" not in dtree["a"].summary
    assert dtree["a"].summary["full"] == "10.5 +/- 2.3, CI: (9.8, 11.2)"
    
    # n should still be present (never used in formatting)
    assert dtree["a"].summary["n"] == 100
    
    # Only 'full' and 'n' should remain
    assert set(dtree["a"].summary.keys()) == {"full", "n"}

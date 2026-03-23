from pyMyriad import DataTree, DataNode, LvlDataNode, SplitDataNode, format_statistics
import pytest


def test_format_statistics_basic():
    """Test basic formatting with kwargs."""
    dtree = DataTree(a=DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}))

    result = format_statistics(dtree, result="{m} +/- {sd}", inplace=True)

    assert result is dtree  # Should return same object when inplace=True
    assert "result" in dtree["a"].summary
    assert dtree["a"].summary["result"] == "10.5 +/- 2.3"
    # Original statistics should still be there
    assert dtree["a"].summary["m"] == 10.5
    assert dtree["a"].summary["sd"] == 2.3


def test_format_statistics_multiple_formats():
    """Test multiple format specifications at once."""
    dtree = DataTree(
        a=DataNode(label="Stats", summary={"m": 10.5, "sd": 2.3, "n": 100})
    )

    format_statistics(
        dtree,
        mean_sd="{m} +/- {sd}",
        sample_size="N={n}",
        mean_only="{m:.2f}",
        inplace=True,
    )

    assert dtree["a"].summary["mean_sd"] == "10.5 +/- 2.3"
    assert dtree["a"].summary["sample_size"] == "N=100"
    assert dtree["a"].summary["mean_only"] == "10.50"


def test_format_statistics_label_filter():
    """Test applying format only to nodes with specific label."""
    dtree = DataTree(
        a=DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}),
        b=DataNode(label="Median", summary={"m": 12.0, "sd": 3.1}),
    )

    format_statistics(dtree, label="Mean", result="{m} ± {sd}", inplace=True)

    # Only node with label="Mean" should have the result
    assert "result" in dtree["a"].summary
    assert dtree["a"].summary["result"] == "10.5 ± 2.3"

    # Node with label="Median" should not have result
    assert "result" not in dtree["b"].summary


def test_format_statistics_all_nodes():
    """Test applying format to all nodes when label=None."""
    dtree = DataTree(
        a=DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}),
        b=DataNode(label="Median", summary={"m": 12.0, "sd": 3.1}),
    )

    format_statistics(dtree, formatted="{m} +/- {sd}", inplace=True)

    # Both nodes should have the formatted statistic
    assert dtree["a"].summary["formatted"] == "10.5 +/- 2.3"
    assert dtree["b"].summary["formatted"] == "12.0 +/- 3.1"


def test_format_statistics_nested():
    """Test formatting in nested tree structure."""
    dtree = DataTree(
        s=SplitDataNode(
            split_var="VAR",
            lvl1=LvlDataNode(
                split_lvl="Level1",
                group1=DataNode(label="Group 1", summary={"mean": 10.2, "sd": 1.5}),
                group2=DataNode(label="Group 2", summary={"mean": 20.8, "sd": 3.2}),
            ),
        )
    )

    format_statistics(dtree, formatted="{mean} ± {sd}", inplace=True)

    assert dtree["s"]["lvl1"]["group1"].summary["formatted"] == "10.2 ± 1.5"
    assert dtree["s"]["lvl1"]["group2"].summary["formatted"] == "20.8 ± 3.2"


def test_format_statistics_no_kwargs_error():
    """Test that error is raised when no format specifications are provided."""
    dtree = DataTree(a=DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}))

    with pytest.raises(
        ValueError, match="At least one format specification must be provided"
    ):
        format_statistics(dtree)


def test_format_statistics_missing_stat_error():
    """Test that error is raised when format references non-existent statistic with safe=True."""
    dtree = DataTree(a=DataNode(label="Mean", summary={"m": 10.5}))

    with pytest.raises(KeyError, match="non-existent statistic"):
        format_statistics(dtree, result="{m} +/- {sd}", safe=True, inplace=True)


def test_format_statistics_numeric_formatting():
    """Test numeric formatting options."""
    dtree = DataTree(a=DataNode(label="Mean", summary={"m": 10.523456, "sd": 2.3789}))

    format_statistics(dtree, rounded="{m:.2f} +/- {sd:.2f}", inplace=True)

    assert dtree["a"].summary["rounded"] == "10.52 +/- 2.38"


def test_format_statistics_no_summary():
    """Test that nodes without summary are handled gracefully."""
    dtree = DataTree(
        a=DataNode(label="NoStats", summary=None),
        b=DataNode(label="WithStats", summary={"m": 10.5, "sd": 2.3}),
    )

    format_statistics(dtree, result="{m} +/- {sd}", inplace=True)

    # Node with no summary should be unchanged
    assert dtree["a"].summary is None
    # Node with summary should be formatted
    assert dtree["b"].summary["result"] == "10.5 +/- 2.3"


def test_format_statistics_inplace_false():
    """Test that inplace=False creates a copy and leaves original unchanged."""
    dtree = DataTree(a=DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}))

    original_summary = dtree["a"].summary.copy()

    # Format with inplace=False (default)
    new_dtree = format_statistics(dtree, result="{m} +/- {sd}")

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
    dtree = DataTree(a=DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}))

    # Format with inplace=True
    result = format_statistics(dtree, result="{m} +/- {sd}", inplace=True)

    # Should return the same object
    assert result is dtree

    # Original should be modified
    assert "result" in dtree["a"].summary
    assert dtree["a"].summary["result"] == "10.5 +/- 2.3"


def test_format_statistics_remove_original():
    """Test that original statistics are removed when remove_original=True."""
    dtree = DataTree(a=DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3, "n": 100}))

    format_statistics(dtree, result="{m} +/- {sd}", remove_original=True, inplace=True)

    # Original statistics used in format should be removed
    assert "m" not in dtree["a"].summary
    assert "sd" not in dtree["a"].summary
    # Statistics not used in format should be preserved
    assert dtree["a"].summary["n"] == 100
    # Formatted result should be present
    assert dtree["a"].summary["result"] == "10.5 +/- 2.3"


def test_format_statistics_remove_original_multiple_formats():
    """Test that only statistics used in each format string are removed."""
    dtree = DataTree(
        a=DataNode(
            label="Stats", summary={"mean": 45.2, "sd": 8.7, "median": 44.5, "n": 150}
        )
    )

    format_statistics(
        dtree,
        formatted="{mean:.1f} ± {sd:.1f}",
        sample_size="N={n}",
        remove_original=True,
        inplace=True,
    )

    # Used statistics should be removed
    assert "mean" not in dtree["a"].summary
    assert "sd" not in dtree["a"].summary
    assert "n" not in dtree["a"].summary  # Used in sample_size format

    # Unused statistics should be preserved
    assert dtree["a"].summary["median"] == 44.5

    # Formatted results should be present
    assert dtree["a"].summary["formatted"] == "45.2 ± 8.7"
    assert dtree["a"].summary["sample_size"] == "N=150"


def test_format_statistics_multiple_rounds():
    """Test multiple rounds of formatting."""
    dtree = DataTree(
        a=DataNode(
            label="Data",
            summary={"m": 10.5, "sd": 2.3, "ci_lower": 9.8, "ci_upper": 11.2},
        )
    )

    # First round: create mean_sd
    format_statistics(dtree, mean_sd="{m} +/- {sd}", inplace=True)
    assert dtree["a"].summary["mean_sd"] == "10.5 +/- 2.3"

    # Second round: create ci_range
    format_statistics(dtree, ci_range="({ci_lower}, {ci_upper})", inplace=True)
    assert dtree["a"].summary["ci_range"] == "(9.8, 11.2)"

    # Third round: combine both
    format_statistics(dtree, full="{mean_sd}, CI: {ci_range}", inplace=True)
    assert dtree["a"].summary["full"] == "10.5 +/- 2.3, CI: (9.8, 11.2)"

    # All intermediate statistics should still be present
    assert "m" in dtree["a"].summary
    assert "sd" in dtree["a"].summary
    assert "ci_lower" in dtree["a"].summary
    assert "ci_upper" in dtree["a"].summary


def test_format_statistics_multiple_rounds_with_removal():
    """Test multiple rounds of formatting with removal of intermediates."""
    dtree = DataTree(
        a=DataNode(
            label="Data",
            summary={"m": 10.5, "sd": 2.3, "ci_lower": 9.8, "ci_upper": 11.2, "n": 100},
        )
    )

    # First round: create mean_sd, remove originals
    format_statistics(dtree, mean_sd="{m} +/- {sd}", remove_original=True, inplace=True)
    assert "m" not in dtree["a"].summary
    assert "sd" not in dtree["a"].summary
    assert dtree["a"].summary["mean_sd"] == "10.5 +/- 2.3"

    # Second round: create ci_range, remove originals
    format_statistics(
        dtree, ci_range="({ci_lower}, {ci_upper})", remove_original=True, inplace=True
    )
    assert "ci_lower" not in dtree["a"].summary
    assert "ci_upper" not in dtree["a"].summary
    assert dtree["a"].summary["ci_range"] == "(9.8, 11.2)"

    # Third round: combine both, remove intermediates
    format_statistics(
        dtree, full="{mean_sd}, CI: {ci_range}", remove_original=True, inplace=True
    )
    assert "mean_sd" not in dtree["a"].summary
    assert "ci_range" not in dtree["a"].summary
    assert dtree["a"].summary["full"] == "10.5 +/- 2.3, CI: (9.8, 11.2)"

    # n should still be present (never used in formatting)
    assert dtree["a"].summary["n"] == 100

    # Only 'full' and 'n' should remain
    assert set(dtree["a"].summary.keys()) == {"full", "n"}


def test_format_statistics_safe_false_default(capsys):
    """Test that safe=False (default) prints warning and skips node when formatting fails."""
    dtree = DataTree(
        a=DataNode(label="Mean", summary={"m": 10.5}),
        b=DataNode(label="Complete", summary={"m": 12.0, "sd": 3.1}),
    )

    # Default safe=False should not raise error
    format_statistics(dtree, result="{m} +/- {sd}", inplace=True)

    # Check that warning was printed
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "'sd'" in captured.out
    assert "Mean" in captured.out

    # Node with missing statistic should not have the result
    assert "result" not in dtree["a"].summary
    # Original statistics should still be there
    assert dtree["a"].summary["m"] == 10.5

    # Node with complete statistics should have the result
    assert dtree["b"].summary["result"] == "12.0 +/- 3.1"


def test_format_statistics_safe_true():
    """Test that safe=True raises error when formatting fails."""
    dtree = DataTree(a=DataNode(label="Mean", summary={"m": 10.5}))

    # safe=True should raise KeyError
    with pytest.raises(KeyError, match="non-existent statistic"):
        format_statistics(dtree, result="{m} +/- {sd}", safe=True, inplace=True)


def test_format_statistics_safe_false_mixed_nodes(capsys):
    """Test safe=False with multiple nodes, some failing and some succeeding."""
    dtree = DataTree(
        a=DataNode(label="Incomplete1", summary={"m": 10.5}),
        b=DataNode(label="Complete", summary={"m": 12.0, "sd": 3.1}),
        c=DataNode(label="Incomplete2", summary={"m": 8.2, "n": 50}),
    )

    format_statistics(dtree, result="{m} +/- {sd}", inplace=True)

    # Check warnings for both incomplete nodes
    captured = capsys.readouterr()
    assert captured.out.count("Warning") == 2

    # Incomplete nodes should not have the result
    assert "result" not in dtree["a"].summary
    assert "result" not in dtree["c"].summary

    # Complete node should have the result
    assert dtree["b"].summary["result"] == "12.0 +/- 3.1"

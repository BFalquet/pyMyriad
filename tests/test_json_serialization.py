"""Tests for AnalysisTree JSON serialization / deserialization."""

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from pyMyriad import AnalysisTree, SplitNode, AnalysisNode
from pyMyriad.analysis_tree import CrossAnalysisNode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_df():
    return pd.DataFrame(
        {
            "A": [10, 20, 30, 40, 50, 60],
            "B": [10, 20, 40, 50, 60, 100],
            "Gender": ["M", "F", "M", "F", "M", "F"],
        }
    )


ENVIRON = {"np": np, "pd": pd}


# ---------------------------------------------------------------------------
# 1. Empty tree round-trip
# ---------------------------------------------------------------------------


def test_empty_tree_round_trip():
    tree = AnalysisTree()
    d = tree.to_dict()
    assert d == {"type": "AnalysisTree", "denom": None, "nodes": []}
    rt = AnalysisTree.from_dict(d)
    assert isinstance(rt, AnalysisTree)
    assert len(rt) == 0
    assert rt.denom is None


# ---------------------------------------------------------------------------
# 2. AnalysisNode-only round-trip (string expressions)
# ---------------------------------------------------------------------------


def test_analysis_node_only_round_trip():
    tree = AnalysisTree().analyze_by(mean="np.mean(df.A)", n="len(df)", label="stats")
    rt = AnalysisTree.from_dict(tree.to_dict())
    assert len(rt) == 1
    node = rt[0]
    assert isinstance(node, AnalysisNode)
    assert node.label == "stats"
    assert node.termination is True
    assert set(node.analysis.keys()) == {"mean", "n"}
    assert node.analysis["mean"] == "np.mean(df.A)"


# ---------------------------------------------------------------------------
# 3. SplitNode with expr round-trip
# ---------------------------------------------------------------------------


def test_split_expr_round_trip():
    tree = AnalysisTree().split_by("df.A > 20", label="A_split").analyze_by(n="len(df)")
    d = tree.to_dict()
    split_dict = d["nodes"][0]
    assert split_dict["type"] == "SplitNode"
    assert split_dict["expr"] == "df.A > 20"
    assert split_dict["label"] == "A_split"
    assert split_dict["drop_empty"] is False

    rt = AnalysisTree.from_dict(d)
    assert isinstance(rt[0], SplitNode)
    assert rt[0].expr == "df.A > 20"
    assert rt[0].label == "A_split"


# ---------------------------------------------------------------------------
# 4. SplitNode with kwexpr round-trip
# ---------------------------------------------------------------------------


def test_split_kwexpr_round_trip():
    tree = (
        AnalysisTree()
        .split_by(high="df.A > 30", low="df.A <= 30")
        .analyze_by(mean="np.mean(df.A)")
    )
    d = tree.to_dict()
    split_dict = d["nodes"][0]
    assert split_dict["type"] == "SplitNode"
    assert "kwexpr" in split_dict
    assert split_dict["kwexpr"] == {"high": "df.A > 30", "low": "df.A <= 30"}

    rt = AnalysisTree.from_dict(d)
    assert rt[0].kwexpr == {"high": "df.A > 30", "low": "df.A <= 30"}


# ---------------------------------------------------------------------------
# 5. Nested splits round-trip
# ---------------------------------------------------------------------------


def test_nested_splits_round_trip():
    tree = (
        AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .split_by("df.A > 30", label="A_split")
        .analyze_by(mean="np.mean(df.A)", label="stats")
    )
    json_str = tree.to_json()
    rt = AnalysisTree.from_json(json_str)

    # Outer split
    assert isinstance(rt[0], SplitNode)
    assert rt[0].label == "Gender"
    # Inner split
    inner = rt[0][0]
    assert isinstance(inner, SplitNode)
    assert inner.label == "A_split"
    # Analysis at leaves
    leaf = inner[0]
    assert isinstance(leaf, AnalysisNode)
    assert leaf.label == "stats"


# ---------------------------------------------------------------------------
# 6. CrossAnalysisNode round-trip
# ---------------------------------------------------------------------------


def test_cross_analysis_round_trip():
    tree = (
        AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .analyze_by(mean="np.mean(df.A)", label="stats")
        .cross_analyze_by(
            diff="np.mean(df.A) - np.mean(ref_df.A)",
            label="cross",
            ref_lvl="M",
        )
    )
    d = tree.to_dict()
    # The cross node is nested inside the SplitNode
    split_dict = d["nodes"][0]
    cross_nodes = [n for n in split_dict["nodes"] if n["type"] == "CrossAnalysisNode"]
    assert len(cross_nodes) == 1
    assert cross_nodes[0]["ref_lvl"] == "M"
    assert "diff" in cross_nodes[0]["analysis"]

    rt = AnalysisTree.from_dict(d)
    cross_node = next(n for n in rt[0] if isinstance(n, CrossAnalysisNode))
    assert cross_node.ref_lvl == "M"
    assert cross_node.analysis["diff"] == "np.mean(df.A) - np.mean(ref_df.A)"


# ---------------------------------------------------------------------------
# 7. Lambda body extraction
# ---------------------------------------------------------------------------


def test_lambda_serialized_as_body():
    tree = (
        AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .analyze_by(
            mean_a=lambda df: np.mean(df.A),
            count=lambda df: len(df),
        )
    )
    d = tree.to_dict()
    analysis = d["nodes"][0]["nodes"][0]["analysis"]
    # Lambda bodies, not full lambda expressions
    assert "lambda" not in analysis["mean_a"]
    assert "np.mean(df.A)" in analysis["mean_a"]
    assert "lambda" not in analysis["count"]
    assert "len(df)" in analysis["count"]


# ---------------------------------------------------------------------------
# 8. denom preserved
# ---------------------------------------------------------------------------


def test_denom_preserved():
    tree = AnalysisTree(denom="A").split_by("df.Gender").analyze_by(n="len(df)")
    d = tree.to_dict()
    assert d["denom"] == "A"
    rt = AnalysisTree.from_dict(d)
    assert rt.denom == "A"

    # Also test list denom
    tree2 = AnalysisTree(denom=["A", "B"]).analyze_by(n="len(df)")
    d2 = tree2.to_dict()
    assert d2["denom"] == ["A", "B"]
    rt2 = AnalysisTree.from_dict(d2)
    assert rt2.denom == ["A", "B"]


# ---------------------------------------------------------------------------
# 9. to_json writes to file
# ---------------------------------------------------------------------------


def test_to_json_file_write():
    tree = AnalysisTree().split_by("df.Gender").analyze_by(n="len(df)")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
    try:
        returned_str = tree.to_json(path=path)
        assert os.path.isfile(path)
        with open(path, "r", encoding="utf-8") as f:
            file_contents = f.read()
        assert file_contents == returned_str
        parsed = json.loads(file_contents)
        assert parsed["type"] == "AnalysisTree"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# 10. from_json reads from file path
# ---------------------------------------------------------------------------


def test_from_json_file_read():
    tree = AnalysisTree().split_by("df.Gender", label="G").analyze_by(n="len(df)")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
    try:
        tree.to_json(path=path)
        loaded = AnalysisTree.from_json(path)
        assert isinstance(loaded, AnalysisTree)
        assert isinstance(loaded[0], SplitNode)
        assert loaded[0].label == "G"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# 11. from_json accepts a raw JSON string
# ---------------------------------------------------------------------------


def test_from_json_string():
    tree = AnalysisTree().analyze_by(mean="np.mean(df.A)", label="mynode")
    json_str = tree.to_json()
    loaded = AnalysisTree.from_json(json_str)
    assert isinstance(loaded, AnalysisTree)
    assert loaded[0].label == "mynode"
    assert loaded[0].analysis["mean"] == "np.mean(df.A)"


# ---------------------------------------------------------------------------
# 12. Deserialized tree is runnable
# ---------------------------------------------------------------------------


def test_deserialized_tree_is_runnable(simple_df):
    tree = (
        AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .analyze_by(
            mean_a=lambda df: np.mean(df.A),
            n=lambda df: len(df),
            label="stats",
        )
    )
    original_result = tree.run(simple_df)

    rt = AnalysisTree.from_json(tree.to_json())
    rt_result = rt.run(simple_df, environ=ENVIRON)

    # Compare computed values for each gender group
    for gender in ["M", "F"]:
        orig_summary = original_result["Gender"][gender]["stats"].summary
        rt_summary = rt_result["Gender"][gender]["stats"].summary
        assert pytest.approx(float(orig_summary["mean_a"])) == float(
            rt_summary["mean_a"]
        )
        assert orig_summary["n"] == rt_summary["n"]


# ---------------------------------------------------------------------------
# 13. Invalid JSON raises JSONDecodeError
# ---------------------------------------------------------------------------


def test_invalid_json_raises():
    with pytest.raises(json.JSONDecodeError):
        AnalysisTree.from_json("this is not valid json {{")

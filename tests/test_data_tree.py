import json
import tempfile

import numpy as np
import pandas as pd
import pytest

from pyMyriad import AnalysisTree, DataTree, DataNode, LvlDataNode, SplitDataNode
from pyMyriad.data_tree import _serialize_summary_value


def test_data_tree_empty():
    dt = DataTree()
    assert isinstance(dt, DataTree)
    assert len(dt) == 0
    assert str(dt) == "Data Tree\n"


def test_data_node():
    dn = DataNode(data=[1, 2, 3], summary={"mean": 2}, label="MyData", depth=1)
    assert isinstance(dn, DataNode)
    assert dn.data == [1, 2, 3]
    assert dn.summary == {"mean": 2}
    assert dn.label == "MyData"
    assert dn.depth == 1
    assert str(dn) == "└─ analysis: MyData\n   └─ mean: 2\n"


def test_lvl_data_node():
    dn1 = DataNode(data=[1, 2, 3], summary={"mean": 2}, label="MyData1", depth=1)
    dn2 = DataNode(data=[4, 5, 6], summary={"mean": 5}, label="MyData2", depth=1)
    ldn = LvlDataNode(dn1=dn1, dn2=dn2, split_lvl="Level1", meta={"info": "test"})

    assert isinstance(ldn, LvlDataNode)
    assert ldn.split_lvl == "Level1"
    assert ldn.meta == {"info": "test"}
    assert len(ldn) == 2
    assert "dn1" in ldn
    assert "dn2" in ldn
    assert (
        str(ldn)
        == "└─ Level1\n   ├─ analysis: MyData1\n   │  └─ mean: 2\n   └─ analysis: MyData2\n      └─ mean: 5\n"
    )


def test_split_data_node():
    dn1 = DataNode(data=[1, 2, 3], summary={"mean": 2}, label="MyData1", depth=1)
    dn2 = DataNode(data=[4, 5, 6], summary={"mean": 5}, label="MyData2", depth=1)
    ldn = LvlDataNode(dn1=dn1, dn2=dn2, split_lvl="Level1", meta={"info": "test"})
    sdn = SplitDataNode(split_var="Var1", T=ldn)

    assert isinstance(sdn, SplitDataNode)
    assert sdn.split_var == "Var1"
    assert len(sdn) == 1
    assert "T" in sdn
    assert (
        str(sdn)
        == "└─ Split: Var1\n   └─ Level1\n      ├─ analysis: MyData1\n      │  └─ mean: 2\n      └─ analysis: MyData2\n         └─ mean: 5\n"
    )


def test_lvl_data_node_with_N_list():
    """LvlDataNode stores _N as a list when provided."""
    dn = DataNode(data=[1, 2, 3], summary={"mean": 2}, label="MyData", depth=1)
    ldn = LvlDataNode(dn=dn, split_lvl="Level1", _N=[3, 2])
    assert ldn._N == [3, 2]


def test_data_node_with_N_list():
    """DataNode stores _N as a list when provided."""
    dn = DataNode(data=[1, 2], summary={"n": 2}, label="L", _N=[5, 3])
    assert dn._N == [5, 3]


def test_data_tree_with_N_list():
    """DataTree stores _N as a list when provided."""
    dn = DataNode(data=[1], summary={"n": 1}, label="L")
    ldn = LvlDataNode(dn=dn, split_lvl="A")
    sdn = SplitDataNode(split_var="Var", A=ldn)
    dt = DataTree(_N=[4], Var=sdn)
    assert dt._N == [4]


# ---------------------------------------------------------------------------
# JSON serialization helpers
# ---------------------------------------------------------------------------


def test_serialize_none():
    assert _serialize_summary_value(None) is None


def test_serialize_bool():
    assert _serialize_summary_value(True) is True
    assert _serialize_summary_value(False) is False


def test_serialize_str():
    assert _serialize_summary_value("hello") == "hello"


def test_serialize_int():
    assert _serialize_summary_value(42) == 42
    assert isinstance(_serialize_summary_value(42), int)


def test_serialize_float():
    assert _serialize_summary_value(3.14) == pytest.approx(3.14)


def test_serialize_nan():
    assert _serialize_summary_value(float("nan")) == "NaN"


def test_serialize_inf():
    assert _serialize_summary_value(float("inf")) == "Infinity"
    assert _serialize_summary_value(float("-inf")) == "-Infinity"


def test_serialize_numpy_int():
    val = np.int64(7)
    result = _serialize_summary_value(val)
    assert result == 7
    assert isinstance(result, int)


def test_serialize_numpy_float():
    val = np.float64(2.5)
    result = _serialize_summary_value(val)
    assert result == pytest.approx(2.5)
    assert isinstance(result, float)


def test_serialize_numpy_nan():
    assert _serialize_summary_value(np.float64("nan")) == "NaN"


def test_serialize_numpy_inf():
    assert _serialize_summary_value(np.float64("inf")) == "Infinity"
    assert _serialize_summary_value(np.float64("-inf")) == "-Infinity"


def test_serialize_numpy_array_falls_back_to_str():
    arr = np.array([1, 2, 3])
    result = _serialize_summary_value(arr)
    assert isinstance(result, str)
    assert "1" in result


# ---------------------------------------------------------------------------
# DataNode.to_dict
# ---------------------------------------------------------------------------


def test_data_node_to_dict_basic():
    dn = DataNode(data=[1, 2, 3], summary={"mean": 2.0, "n": 3}, label="stats", depth=1)
    d = dn.to_dict()
    assert d["type"] == "DataNode"
    assert d["label"] == "stats"
    assert d["summary"]["mean"] == pytest.approx(2.0)
    assert d["summary"]["n"] == 3
    assert d["_N"] is None


def test_data_node_to_dict_with_N():
    dn = DataNode(data=None, summary={"n": 1}, label="L", _N=[10, 5])
    d = dn.to_dict()
    assert d["_N"] == [10, 5]


def test_data_node_to_dict_nan_inf():
    dn = DataNode(
        data=None,
        summary={
            "nan_val": float("nan"),
            "inf_val": float("inf"),
            "ninf_val": float("-inf"),
        },
        label="edge",
    )
    d = dn.to_dict()
    assert d["summary"]["nan_val"] == "NaN"
    assert d["summary"]["inf_val"] == "Infinity"
    assert d["summary"]["ninf_val"] == "-Infinity"


def test_data_node_to_dict_numpy_scalar():
    dn = DataNode(
        data=None,
        summary={"mean": np.float64(3.5), "count": np.int64(4)},
        label="np",
    )
    d = dn.to_dict()
    # Must be JSON-serializable
    json.dumps(d)
    assert d["summary"]["mean"] == pytest.approx(3.5)
    assert d["summary"]["count"] == 4


def test_data_node_to_dict_empty_summary():
    dn = DataNode(data=None, summary={}, label="empty")
    d = dn.to_dict()
    assert d["summary"] == {}


def test_data_node_to_dict_none_summary():
    dn = DataNode(data=None, summary=None, label="no_summary")
    d = dn.to_dict()
    assert d["summary"] == {}


# ---------------------------------------------------------------------------
# SplitDataNode.to_dict
# ---------------------------------------------------------------------------


def test_split_data_node_to_dict():
    dn = DataNode(data=None, summary={"n": 3}, label="stats")
    ldn = LvlDataNode(stats=dn, split_lvl="Male")
    sdn = SplitDataNode(split_var="df.Gender", Male=ldn)
    d = sdn.to_dict()
    assert d["type"] == "SplitDataNode"
    assert d["split_var"] == "df.Gender"
    assert "label" in d
    assert "Male" in d["children"]
    assert d["children"]["Male"]["type"] == "LvlDataNode"


# ---------------------------------------------------------------------------
# LvlDataNode.to_dict
# ---------------------------------------------------------------------------


def test_lvl_data_node_to_dict():
    dn = DataNode(data=None, summary={"n": 2}, label="stats")
    ldn = LvlDataNode(stats=dn, split_lvl="Female", _N=[10, 4])
    d = ldn.to_dict()
    assert d["type"] == "LvlDataNode"
    assert d["split_lvl"] == "Female"
    assert d["_N"] == [10, 4]
    assert "stats" in d["children"]
    assert d["children"]["stats"]["type"] == "DataNode"


# ---------------------------------------------------------------------------
# DataTree.to_dict / to_json
# ---------------------------------------------------------------------------


def test_data_tree_to_dict_empty():
    dt = DataTree()
    d = dt.to_dict()
    assert d == {"type": "DataTree", "_N": None, "children": {}}


def test_data_tree_to_dict_with_N():
    dn = DataNode(data=None, summary={"n": 1}, label="L")
    ldn = LvlDataNode(dn=dn, split_lvl="A")
    sdn = SplitDataNode(split_var="Var", A=ldn)
    dt = DataTree(_N=[5], Var=sdn)
    d = dt.to_dict()
    assert d["_N"] == [5]
    assert "Var" in d["children"]


def test_data_tree_to_json_returns_valid_json():
    dn = DataNode(data=None, summary={"mean": 4.2}, label="stats")
    ldn = LvlDataNode(stats=dn, split_lvl="A")
    sdn = SplitDataNode(split_var="Grp", A=ldn)
    dt = DataTree(Grp=sdn)
    json_str = dt.to_json()
    parsed = json.loads(json_str)
    assert parsed["type"] == "DataTree"
    assert parsed["children"]["Grp"]["type"] == "SplitDataNode"


def test_data_tree_to_json_writes_file():
    dn = DataNode(data=None, summary={"n": 1}, label="L")
    ldn = LvlDataNode(dn=dn, split_lvl="A")
    sdn = SplitDataNode(split_var="Var", A=ldn)
    dt = DataTree(Var=sdn)
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        tmp_path = f.name
    json_str = dt.to_json(path=tmp_path)
    with open(tmp_path, "r") as f:
        file_content = f.read()
    assert file_content == json_str
    assert json.loads(file_content)["type"] == "DataTree"


def test_data_tree_to_json_indent():
    dt = DataTree()
    assert "\n" in dt.to_json(indent=2)  # indented output has newlines


# ---------------------------------------------------------------------------
# Integration: run AnalysisTree → DataTree.to_json
# ---------------------------------------------------------------------------


ENVIRON = {"np": np, "pd": pd}


@pytest.fixture
def simple_df():
    return pd.DataFrame(
        {
            "A": [10, 20, 30, 40, 50, 60],
            "Gender": ["M", "F", "M", "F", "M", "F"],
        }
    )


def test_integration_to_dict_structure(simple_df):
    tree = (
        AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .analyze_by(n="len(df)", mean_a="np.mean(df.A)", label="stats")
    )
    result = tree.run(simple_df, environ=ENVIRON)
    d = result.to_dict()

    assert d["type"] == "DataTree"
    gender_split = d["children"]["Gender"]
    assert gender_split["type"] == "SplitDataNode"
    assert gender_split["split_var"] == "df.Gender"

    # Each level exists
    for lvl_key, lvl_node in gender_split["children"].items():
        assert lvl_node["type"] == "LvlDataNode"
        stats_node = lvl_node["children"]["stats"]
        assert stats_node["type"] == "DataNode"
        assert "n" in stats_node["summary"]
        assert "mean_a" in stats_node["summary"]


def test_integration_to_json_parseable(simple_df):
    tree = (
        AnalysisTree()
        .split_by("df.Gender", label="Gender")
        .analyze_by(n="len(df)", mean_a="np.mean(df.A)", label="stats")
    )
    result = tree.run(simple_df, environ=ENVIRON)
    json_str = result.to_json()
    parsed = json.loads(json_str)
    assert parsed["type"] == "DataTree"


def test_integration_numpy_scalars_serializable(simple_df):
    """numpy scalars in summary must survive json.dumps without error."""
    tree = AnalysisTree().analyze_by(
        mean=lambda df: np.mean(df.A), count=lambda df: len(df)
    )
    result = tree.run(simple_df, environ=ENVIRON)
    # Should not raise
    json_str = result.to_json()
    parsed = json.loads(json_str)
    # A simple (no-split) tree stores the DataNode as a direct child of DataTree.
    # The key is the AnalysisNode label; grab the first (and only) child.
    child = next(iter(parsed["children"].values()))
    summary = child["summary"]
    assert "mean" in summary
    assert "count" in summary
    # Values must be native Python types after JSON round-trip
    assert isinstance(summary["count"], int)
    assert isinstance(summary["mean"], float)


def test_integration_nan_in_summary():
    """NaN in summary becomes the string 'NaN' in JSON output."""
    df = pd.DataFrame({"A": [float("nan"), float("nan")]})
    tree = AnalysisTree().analyze_by(mean="np.mean(df.A.values)")
    result = tree.run(df, environ=ENVIRON)
    parsed = json.loads(result.to_json())
    # Grab the single DataNode child regardless of its label key
    child = next(iter(parsed["children"].values()))
    summary = child["summary"]
    assert summary["mean"] == "NaN"

from pyMyriad import AnalysisTree, SplitNode, AnalysisNode, DataTree
import pandas as pd
import numpy as np
from importlib import import_module
from contextlib import contextmanager

@contextmanager
def with_module(module_name, module_abr):
    """Temporarily provide an environment with a specific module available."""
    try:
        # Import the requested module
        module = import_module(module_name)
        # Create environment with just this module
        environ = {module_abr: module}
        yield environ
    finally:
        pass

def test_run_simple():
    a_node = AnalysisNode(m = "1", s = "2") # no eval in analysis
    s_node = SplitNode(a_node, a_node, expr = "df.B > 50")
    a_tree = AnalysisTree(s_node, a_node)
    df = pd.DataFrame({
        "A": [10, 11, 12, 14, 15, 16],
        "B": [10, 20, 40 ,50 ,60, 100]
    })

    res = a_tree.run(df)
    assert isinstance(res, DataTree)
    assert len(res) == 2
    assert list(res.keys()) == ["df.B > 50", "Custom"]
    assert len(res["df.B > 50"]) == 2
    assert len(res["Custom"].summary) == 2

def test_run_eval_in_analysis():
    a_node = AnalysisNode(m = "np.mean(df.A)", s = "np.std(df.B)")
    df = pd.DataFrame({
        "A": [10, 20],
        "B": [10, 10]
    })
    with with_module('numpy', 'np') as environ:
      res = a_node.run(df, environ = environ)

    assert res.summary == {"m": np.float64(15), "s": np.float64(0)}

def test_run_eval_in_split():
    a_node = AnalysisNode(minB = "np.min(df.B)", minA = "np.min(df.A)")
    s_node = SplitNode(a_node, a_node, gp1 = "df.B > 30", gp2 = "df.B > 50")
    a_tree = AnalysisTree(s_node, a_node)
    df = pd.DataFrame({
        "A": [10, 11, 12, 14, 15, 16],
        "B": [10, 20, 40 ,50 ,60, 100]
    })

    with with_module('numpy', 'np') as environ:
        res = a_tree.run(df, environ = environ)
    assert isinstance(res, DataTree)
    assert len(res) == 2
    assert list(res.keys()) == ["gp1-gp2", "Custom"]
    assert len(res["gp1-gp2"]) == 2
    assert len(res["Custom"].summary) == 2


# --- denom / _N tests ---

def test_denom_N_is_list_at_root():
    """_N at root is a single-element list when denom is set."""
    df = pd.DataFrame({
        "ID":     ["A", "B", "C", "C"],
        "Gender": ["M", "F", "F", "F"],
        "Income": [40000.0, 55000.0, 60000.0, 62000.0],
    })
    a_node = AnalysisNode(n=lambda df: len(df))
    a_tree = AnalysisTree(a_node, denom="ID")
    result = a_tree.run(df)
    assert result._N == [3]  # 3 unique IDs: A, B, C


def test_denom_N_accumulates_across_split():
    """_N grows by one element at each split level."""
    df = pd.DataFrame({
        "ID":     ["A", "B", "C", "C"],
        "Gender": ["M", "F", "F", "F"],
        "Income": [40000.0, 55000.0, 60000.0, 62000.0],
    })
    a_tree = (
        AnalysisTree(denom="ID")
        .split_by("df.Gender")
        .analyze_by(mean_income=lambda df: np.mean(df.Income))
    )
    result = a_tree.run(df)
    # Root _N: 3 unique IDs
    assert result._N == [3]
    split_node = result["df.Gender"]
    # F group: IDs B, C => 2 unique
    assert split_node["F"]._N == [3, 2]
    # M group: ID A => 1 unique
    assert split_node["M"]._N == [3, 1]


def test_denom_lambda_N_only():
    """Lambda that only takes _N receives the count list."""
    df = pd.DataFrame({
        "ID":     ["A", "B", "C", "C"],
        "Gender": ["M", "F", "F", "F"],
        "Income": [40000.0, 55000.0, 60000.0, 62000.0],
    })
    a_tree = (
        AnalysisTree(denom="ID")
        .split_by("df.Gender")
        .analyze_by(prop=lambda _N: _N[-1] / _N[0])
    )
    result = a_tree.run(df)
    assert abs(result["df.Gender"]["F"]["0"].summary["prop"] - 2 / 3) < 1e-9
    assert abs(result["df.Gender"]["M"]["0"].summary["prop"] - 1 / 3) < 1e-9


def test_denom_lambda_df_and_N():
    """Lambda with both df and _N receives both arguments."""
    df = pd.DataFrame({
        "ID":     ["A", "B", "C", "C"],
        "Gender": ["M", "F", "F", "F"],
        "Income": [40000.0, 55000.0, 60000.0, 62000.0],
    })
    a_tree = (
        AnalysisTree(denom="ID")
        .split_by("df.Gender")
        .analyze_by(rows_per_id=lambda df, _N: len(df) / _N[-1])
    )
    result = a_tree.run(df)
    # F group: 3 rows / 2 unique IDs = 1.5
    assert abs(result["df.Gender"]["F"]["0"].summary["rows_per_id"] - 1.5) < 1e-9


def test_denom_string_expr_uses_N():
    """String expressions can reference _N via eval context."""
    df = pd.DataFrame({
        "ID":     ["A", "B", "C", "C"],
        "Gender": ["M", "F", "F", "F"],
        "Income": [40000.0, 55000.0, 60000.0, 62000.0],
    })
    a_tree = (
        AnalysisTree(denom="ID")
        .split_by("df.Gender")
        .analyze_by(prop="_N[-1] / _N[0]")
    )
    result = a_tree.run(df)
    assert abs(result["df.Gender"]["F"]["0"].summary["prop"] - 2 / 3) < 1e-9


def test_denom_none_backward_compat():
    """Without denom, _N is None on all nodes (backward compat)."""
    df = pd.DataFrame({"A": [1, 2, 3], "B": [10, 20, 30]})
    a_tree = AnalysisTree().split_by("df.A > 1").analyze_by(n=lambda df: len(df))
    result = a_tree.run(df)
    assert result._N is None
    for lvl_node in result["df.A > 1"].values():
        assert lvl_node._N is None


def test_denom_list_of_columns():
    """denom as a list of columns counts unique row combinations."""
    df = pd.DataFrame({
        "PatientID": ["P1", "P1", "P2", "P3"],
        "Visit":     [1,    2,    1,    1   ],
        "Value":     [10,   20,   30,   40  ],
    })
    a_node = AnalysisNode(n=lambda df: len(df))
    a_tree = AnalysisTree(a_node, denom=["PatientID", "Visit"])
    result = a_tree.run(df)
    # 3 unique (PatientID, Visit) combinations: (P1,1), (P1,2), (P2,1), (P3,1) => 4
    assert result._N == [4]


# --- drop_empty tests ---

def test_drop_empty_false_keeps_empty_groups():
    """drop_empty=False (default) keeps kwexpr levels with zero rows.

    For expr-based splits, groupby only returns groups that exist in the data,
    so empty groups can only arise from kwexpr-style splits where conditions are
    explicitly defined but never satisfied.
    """
    df = pd.DataFrame({"A": [10, 20, 30]})
    tree = (
        AnalysisTree()
        .split_by(
            high="df.A > 100",   # nobody qualifies → empty DataFrame
            low="df.A <= 100",
            drop_empty=False,
        )
        .analyze_by(n=lambda df: len(df))
    )
    result = tree.run(df)
    split = result["high-low"]
    assert "low" in split
    assert "high" in split  # kept despite having zero rows
    assert len(split["high"]["0"].data) == 0


def test_drop_empty_true_removes_empty_groups():
    """drop_empty=True discards levels that have zero rows."""
    df = pd.DataFrame({
        "A": [10, 20, 30],
        "B": [True, True, True],   # all True → False group will be empty
    })
    tree = (
        AnalysisTree()
        .split_by("df.B", drop_empty=True)
        .analyze_by(n=lambda df: len(df))
    )
    result = tree.run(df)
    split = result["df.B"]
    assert "True" in split
    assert "False" not in split


def test_drop_empty_true_with_kwexpr():
    """drop_empty=True also works with keyword-expression splits."""
    df = pd.DataFrame({
        "Income": [30000, 40000, 50000],
    })
    tree = (
        AnalysisTree()
        .split_by(
            high="df.Income > 100000",   # nobody qualifies → empty
            low="df.Income <= 100000",
            drop_empty=True,
        )
        .analyze_by(n=lambda df: len(df))
    )
    result = tree.run(df)
    split = result["high-low"]
    assert "low" in split
    assert "high" not in split


def test_categorical_dtype_observed_only():
    """Split on pd.Categorical column produces only observed groups (no ghost groups)."""
    df = pd.DataFrame({
        "Gender": pd.Categorical(["M", "M", "M"], categories=["M", "F"]),
        "Income": [50000, 60000, 70000],
    })
    tree = (
        AnalysisTree()
        .split_by("df.Gender")
        .analyze_by(n=lambda df: len(df))
    )
    result = tree.run(df)
    split = result["df.Gender"]
    assert "M" in split
    # "F" has no rows in this data; observed=True means it should not appear
    assert "F" not in split

from pyMyriad import *
from pyMyriad.utils import get_top_globals
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

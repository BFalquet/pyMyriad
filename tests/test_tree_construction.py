import pytest
from pyMyriad import AnalysisTree, AnalysisNode, SplitNode

def test_tree_construction_split_node():

    a_node = AnalysisNode("mean(df.val)")
    s_node = SplitNode(a_node, expr = "df.VAR1")

    assert isinstance(s_node, SplitNode)
    assert len(s_node) == 1

def test_tree_construction_analysis_tree():
    # Combine SplitNode in Analysis Tree
    s_node = SplitNode(expr = "df.VAR1")
    a_tree = AnalysisTree(s_node)

    assert isinstance(a_tree, AnalysisTree)
    assert len(a_tree) == 1

    # Combine multiple Split Node in Analysis Tree
    a_tree_2 = AnalysisTree(s_node, s_node)
    assert isinstance(a_tree, AnalysisTree)
    assert len(a_tree_2) == 2

def test_tree_construction_analysis_tree_mulibranch():
    # Combine SplitNode in Analysis Tree
    a_node = AnalysisNode("mean(df.val)")
    a_node2 = AnalysisNode("sd(df.val)")
    s_node = SplitNode(a_node, a_node2, expr = "df.VAR1")

    s_node2 = SplitNode(a_node, expr = "df.VAR2")

    a_tree = AnalysisTree(s_node, s_node2)

    assert isinstance(a_tree, AnalysisTree)
    assert len(a_tree) == 2

    assert isinstance(a_tree[0], SplitNode)
    assert isinstance(a_tree[1], SplitNode)

# ----

def test_split_by():
    res = AnalysisTree().split_by(m = "A > 50")
    assert isinstance(res, AnalysisTree)
    assert len(res) == 1
    assert isinstance(res[0], SplitNode)
    assert res[0].kwexpr == {"m": "A > 50"}

    res = AnalysisTree().split_by("A > 50")
    assert isinstance(res, AnalysisTree)
    assert len(res) == 1
    assert isinstance(res[0], SplitNode)
    assert res[0].expr == "A > 50"

    # Chaining works as expected
    res = res.split_by(x = "B == 40")
    assert isinstance(res[0], SplitNode)
    assert len(res[0]) == 1
    assert isinstance(res[0][0], SplitNode)
    assert len(res[0][0]) == 0
    assert res[0][0].kwexpr == {"x": "B == 40"}
    
    # Termination prevents addition
    atree = AnalysisTree(AnalysisNode(m = "np.mean(df.B)"))
    atree2 = atree.split_by("X > 10")
    assert atree == atree2

def test_analyze_by():
    res = AnalysisTree().analyze_by(m = "np.mean(df.B)")
    assert isinstance(res, AnalysisTree)
    assert len(res) == 1
    assert isinstance(res[0], AnalysisNode)
    assert res[0].analysis == {"m": "np.mean(df.B)"}

    res = AnalysisTree().split_by("A>50").analyze_by(m = "np.mean(df.B)")
    assert len(res[0]) == 1
    assert isinstance(res[0], SplitNode)
    assert isinstance(res[0][0], AnalysisNode)
    assert res[0][0].analysis == {"m": "np.mean(df.B)"}

    # Termination prevents addition of split node
    res2 = res.split_by("X > 10")
    assert res == res2

    # Termination doesn't prevent addition of analysis node
    res3 = res.analyze_by(s = "np.std(df.B)")
    assert len(res[0]) == 2
    assert isinstance(res[0][0], AnalysisNode)
    assert isinstance(res[0][1], AnalysisNode)

def test_split_at_by():
    res = AnalysisTree().split_by("df.A > 50", label = "A > 50")
    assert isinstance(res[0], SplitNode)

    # Split at the existing split node
    res.split_at_by(path = ["*"], expr = "df.B < 20", label = "B < 20")
    assert len(res) == 1
    assert isinstance(res[0], SplitNode)
    assert len(res[0]) == 1
    assert isinstance(res[0][0], SplitNode)
    assert res[0][0].expr == "df.B < 20"

    # Split at non-existing path does nothing
    res_ori = res.copy()
    res.split_at_by(path = ["NonExisting"], expr = "df.B < 20")
    assert res == res_ori

    # Split at root level
    res.split_at_by(path = [], expr = "df.C == 100", label = "C = 100")
    assert len(res) == 2
    assert isinstance(res[0], SplitNode)
    assert len(res[0]) == 1
    assert isinstance(res[0][0], SplitNode)
    assert res[1].label == "C = 100"

    # Split at second level
    res.split_at_by(path = ["A > 50", "*"], expr = "df.D != 0", label = "D != 0")
    assert isinstance(res[0][0][0], SplitNode)
    assert res[0][0][0].expr == "df.D != 0"

def test_split_at_by_ignores_termination():
    res = AnalysisTree().split_by("df.A > 50", label = "A > 50").analyze_by(m = "np.mean(df.B)")
    res.split_at_by(path = ["A > 50"], expr = "df.B < 20", label = "B < 20")
    assert len(res) == 1
    assert isinstance(res[0], SplitNode)
    assert len(res[0]) == 2
    assert isinstance(res[0][0], AnalysisNode)
    assert isinstance(res[0][1], SplitNode)
    assert res[0][1].expr == "df.B < 20"
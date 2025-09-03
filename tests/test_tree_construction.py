import pytest
from pyMyriade import AnalysisTree, AnalysisNode, SplitNode

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
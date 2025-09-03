import pytest
from pyMyriade.analysis_tree import AnalysisTree, SplitNode, AnalysisNode

# analysis_tree

def test_analysis_tree_initialization_empty():
    tree = AnalysisTree()
    assert isinstance(tree, AnalysisTree)
    assert tree.date == "Today"
    assert list(tree) == []

def test_analysis_tree_str_output():
    tree = AnalysisTree()
    assert str(tree) == "Analysis Tree\n"

# split_node

def test_split_node_initialization_with_expr():
    node = SplitNode(expr = "df.age > 50")
    assert node.expr == "df.age > 50"
    assert node.kwexpr is None

    

def test_split_node_initialization_with_kwargs():
    node = SplitNode(group1 = "df.age > 50", group2 = "df.age <= 50")
    assert node.expr is None
    assert node.kwexpr == {"group1": "df.age > 50", "group2": "df.age <= 50"}
    assert dict(node) == {}

def test_split_node_error():
    with pytest.raises(AssertionError):
        SplitNode()

def test_split_node_error():
    with pytest.raises(AssertionError):
        SplitNode(expr = "df.age > 50", group1 = "df.age > 50", group2 = "df.age <= 50")


# analysis_node

def test_analysis_node_intialization():
    node = AnalysisNode("mean(df.val)")
    assert node.label == ""
    assert node.termination
    assert node.analysis == {"mean(df.val)": "mean(df.val)"}

    node = AnalysisNode("mean(df.val)", "sd(df.val)")
    assert node.label == ""
    assert node.termination
    assert node.analysis == {"mean(df.val)": "mean(df.val)", "sd(df.val)":"sd(df.val)"}

    node = AnalysisNode("mean(df.val)", sd = "sd(df.val)")
    assert node.label == ""
    assert node.termination
    assert node.analysis == {"mean(df.val)": "mean(df.val)", "sd":"sd(df.val)"}

def test_analysis_node_error():
    with pytest.raises(AssertionError):
        AnalysisNode()
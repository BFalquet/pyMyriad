import pytest
import numpy as np
import pandas as pd
from pyMyriad.analysis_tree import AnalysisTree, SplitNode, AnalysisNode

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

def test_split_node_error_both_params():
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

# Function support tests

def test_split_node_with_functions():
    """Test SplitNode initialization with function arguments"""
    # Single function condition
    node = SplitNode(positive_sum = lambda df: (df.A + df.B) > 0)
    assert node.expr is None
    assert "positive_sum" in node.kwexpr
    assert callable(node.kwexpr["positive_sum"])

    # Multiple function conditions
    node = SplitNode(
        high_a = lambda df: df.A > 0.5,
        high_b = lambda df: df.B > 0.5
    )
    assert node.expr is None
    assert len(node.kwexpr) == 2
    assert all(callable(v) for v in node.kwexpr.values())

def test_analysis_node_with_functions():
    """Test AnalysisNode with function-based analysis"""
    # Test with function kwargs
    node = AnalysisNode(
        mean_a = lambda df: np.mean(df.A),
        std_b = lambda df: np.std(df.B),
        count = lambda df: len(df)
    )
    assert len(node.analysis) == 3
    assert all(callable(v) for v in node.analysis.values())

    # Test mixed functions and strings
    node = AnalysisNode(
        func_mean = lambda df: np.mean(df.A),
        str_count = "len(df)"
    )
    assert len(node.analysis) == 2
    assert callable(node.analysis["func_mean"])
    assert isinstance(node.analysis["str_count"], str)

def test_analysis_node_with_positional_functions():
    """Test AnalysisNode with positional function arguments"""
    # This should work but convert to named functions
    func1 = lambda df: np.mean(df.A)
    func2 = lambda df: np.std(df.B)
    
    node = AnalysisNode(func1, func2)
    assert len(node.analysis) == 2
    # Check that functions are stored with generated names
    assert all(callable(v) for v in node.analysis.values())

def test_analysis_tree_function_workflow():
    """Test complete AnalysisTree workflow with functions"""
    # Create sample data
    df = pd.DataFrame({
        'A': np.random.randn(100),
        'B': np.random.randn(100),
        'category': np.random.choice(['X', 'Y'], 100)
    })
    
    # Build tree with functions
    tree = (AnalysisTree()
           .split_by(positive_sum=lambda df: (df.A + df.B) > 0)
           .analyze_by(
               mean_a=lambda df: np.mean(df.A),
               std_b=lambda df: np.std(df.B),
               count=lambda df: len(df)
           ))
    
    # Should be able to run without environ parameter
    result = tree.run(df)
    assert result is not None
    
def test_mixed_string_and_function_approach():
    """Test mixing string expressions and functions"""
    df = pd.DataFrame({
        'A': np.random.randn(50),
        'B': np.random.randn(50)
    })
    
    tree = (AnalysisTree()
           .split_by("df.A > 0")  # String expression
           .analyze_by(
               func_mean=lambda df: np.mean(df.B),  # Function
               str_count="len(df)"  # String expression
           ))
    
    # This should work with environ for string expressions
    environ = {'np': np}
    result = tree.run(df, environ=environ)
    assert result is not None

def test_complex_function_analysis():
    """Test complex function-based analysis"""
    df = pd.DataFrame({
        'A': np.random.randn(30),
        'B': np.random.randn(30),
        'category': np.random.choice(['X', 'Y', 'Z'], 30)
    })
    
    def complex_analysis(df):
        return {
            'mean_a': np.mean(df.A),
            'correlation': np.corrcoef(df.A, df.B)[0, 1] if len(df) > 1 else 0,
            'category_counts': df.category.value_counts().to_dict()
        }
    
    tree = (AnalysisTree()
           .split_by(has_positive_a = lambda df: df.A > 0)
           .analyze_by(
               simple_count = lambda df: len(df),
               complex_stats = complex_analysis
           ))
    
    result = tree.run(df)
    assert result is not None

def test_scope_eval_function_compatibility():
    """Test that scope_eval works with both functions and strings"""
    from pyMyriad.utils import scope_eval
    
    df = pd.DataFrame({
        'A': np.random.randn(20),
        'B': np.random.randn(20)
    })
    
    # Test pure function usage
    result_func = scope_eval(
        df=df,
        mean_a=lambda df: np.mean(df.A),
        std_b=lambda df: np.std(df.B),
        count=lambda df: len(df)
    )
    
    assert len(result_func) == 3
    assert 'mean_a' in result_func
    assert 'std_b' in result_func
    assert 'count' in result_func
    assert result_func['count'] == 20
    
    # Test mixed usage
    result_mixed = scope_eval(
        df=df,
        extra_context = {'np': np},
        func_mean = lambda df: np.mean(df.A),  # Function
        str_count = "len(df)"                  # String
    )
    
    assert len(result_mixed) == 2
    assert 'func_mean' in result_mixed
    assert 'str_count' in result_mixed
    assert result_mixed['str_count'] == 20
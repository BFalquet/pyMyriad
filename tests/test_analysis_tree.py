import pytest
import numpy as np
import pandas as pd
from pyMyriad.analysis_tree import AnalysisTree, SplitNode, AnalysisNode

# analysis_tree


def test_analysis_tree_initialization_empty():
    tree = AnalysisTree()
    assert isinstance(tree, AnalysisTree)
    assert isinstance(tree.att, tuple)
    assert list(tree) == []


def test_analysis_tree_str_output():
    tree = AnalysisTree()
    assert str(tree) == "Analysis Tree\n"


# split_node


def test_split_node_initialization_with_expr():
    node = SplitNode(expr="df.age > 50")
    assert node.expr == "df.age > 50"
    assert node.kwexpr is None


def test_split_node_initialization_with_kwargs():
    node = SplitNode(group1="df.age > 50", group2="df.age <= 50")
    assert node.expr is None
    assert node.kwexpr == {"group1": "df.age > 50", "group2": "df.age <= 50"}
    assert dict(node) == {}


def test_split_node_error():
    with pytest.raises(AssertionError):
        SplitNode()


def test_split_node_error_both_params():
    with pytest.raises(AssertionError):
        SplitNode(expr="df.age > 50", group1="df.age > 50", group2="df.age <= 50")


# analysis_node


def test_analysis_node_intialization():
    node = AnalysisNode("mean(df.val)")
    assert node.label == ""
    assert node.termination
    assert node.analysis == {"mean(df.val)": "mean(df.val)"}

    node = AnalysisNode("mean(df.val)", "sd(df.val)")
    assert node.label == ""
    assert node.termination
    assert node.analysis == {"mean(df.val)": "mean(df.val)", "sd(df.val)": "sd(df.val)"}

    node = AnalysisNode("mean(df.val)", sd="sd(df.val)")
    assert node.label == ""
    assert node.termination
    assert node.analysis == {"mean(df.val)": "mean(df.val)", "sd": "sd(df.val)"}


def test_analysis_node_error():
    with pytest.raises(AssertionError):
        AnalysisNode()


# Function support tests


def test_split_node_with_functions():
    """Test SplitNode initialization with function arguments"""
    # Single function condition
    node = SplitNode(positive_sum=lambda df: (df.A + df.B) > 0)
    assert node.expr is None
    assert "positive_sum" in node.kwexpr
    assert callable(node.kwexpr["positive_sum"])

    # Multiple function conditions
    node = SplitNode(high_a=lambda df: df.A > 0.5, high_b=lambda df: df.B > 0.5)
    assert node.expr is None
    assert len(node.kwexpr) == 2
    assert all(callable(v) for v in node.kwexpr.values())


def test_analysis_node_with_functions():
    """Test AnalysisNode with function-based analysis"""
    # Test with function kwargs
    node = AnalysisNode(
        mean_a=lambda df: np.mean(df.A),
        std_b=lambda df: np.std(df.B),
        count=lambda df: len(df),
    )
    assert len(node.analysis) == 3
    assert all(callable(v) for v in node.analysis.values())

    # Test mixed functions and strings
    node = AnalysisNode(func_mean=lambda df: np.mean(df.A), str_count="len(df)")
    assert len(node.analysis) == 2
    assert callable(node.analysis["func_mean"])
    assert isinstance(node.analysis["str_count"], str)


def test_analysis_node_with_positional_functions():
    """Test AnalysisNode with positional function arguments"""

    # This should work but convert to named functions
    def func1(df):
        return np.mean(df.A)

    def func2(df):
        return np.std(df.B)

    node = AnalysisNode(func1, func2)
    assert len(node.analysis) == 2
    # Check that functions are stored with generated names
    assert all(callable(v) for v in node.analysis.values())


def test_analysis_tree_function_workflow():
    """Test complete AnalysisTree workflow with functions"""
    # Create sample data
    df = pd.DataFrame(
        {
            "A": np.random.randn(100),
            "B": np.random.randn(100),
            "category": np.random.choice(["X", "Y"], 100),
        }
    )

    # Build tree with functions
    tree = (
        AnalysisTree()
        .split_by(positive_sum=lambda df: (df.A + df.B) > 0)
        .analyze_by(
            mean_a=lambda df: np.mean(df.A),
            std_b=lambda df: np.std(df.B),
            count=lambda df: len(df),
        )
    )

    # Should be able to run without environ parameter
    result = tree.run(df)
    assert result is not None


def test_mixed_string_and_function_approach():
    """Test mixing string expressions and functions"""
    df = pd.DataFrame({"A": np.random.randn(50), "B": np.random.randn(50)})

    tree = (
        AnalysisTree()
        .split_by("df.A > 0")  # String expression
        .analyze_by(
            func_mean=lambda df: np.mean(df.B),  # Function
            str_count="len(df)",  # String expression
        )
    )

    # This should work with environ for string expressions
    environ = {"np": np}
    result = tree.run(df, environ=environ)
    assert result is not None


def test_complex_function_analysis():
    """Test complex function-based analysis"""
    df = pd.DataFrame(
        {
            "A": np.random.randn(30),
            "B": np.random.randn(30),
            "category": np.random.choice(["X", "Y", "Z"], 30),
        }
    )

    def complex_analysis(df):
        return {
            "mean_a": np.mean(df.A),
            "correlation": np.corrcoef(df.A, df.B)[0, 1] if len(df) > 1 else 0,
            "category_counts": df.category.value_counts().to_dict(),
        }

    tree = (
        AnalysisTree()
        .split_by(has_positive_a=lambda df: df.A > 0)
        .analyze_by(simple_count=lambda df: len(df), complex_stats=complex_analysis)
    )

    result = tree.run(df)
    assert result is not None


def test_scope_eval_function_compatibility():
    """Test that scope_eval works with both functions and strings"""
    from pyMyriad.utils import scope_eval

    df = pd.DataFrame({"A": np.random.randn(20), "B": np.random.randn(20)})

    # Test pure function usage
    result_func = scope_eval(
        df=df,
        mean_a=lambda df: np.mean(df.A),
        std_b=lambda df: np.std(df.B),
        count=lambda df: len(df),
    )

    assert len(result_func) == 3
    assert "mean_a" in result_func
    assert "std_b" in result_func
    assert "count" in result_func
    assert result_func["count"] == 20

    # Test mixed usage
    result_mixed = scope_eval(
        df=df,
        extra_context={"np": np},
        func_mean=lambda df: np.mean(df.A),  # Function
        str_count="len(df)",  # String
    )

    assert len(result_mixed) == 2
    assert "func_mean" in result_mixed
    assert "str_count" in result_mixed
    assert result_mixed["str_count"] == 20


# CrossAnalysisNode tests


def test_cross_analysis_node_initialization():
    """Test CrossAnalysisNode initialization"""
    from pyMyriad.analysis_tree import CrossAnalysisNode

    node = CrossAnalysisNode(
        mean_diff="np.mean(df.A) - np.mean(ref_df.A)", ref_lvl="reference"
    )
    assert node.label == ""
    assert node.ref_lvl == "reference"
    assert node.termination
    assert "mean_diff" in node.analysis


def test_cross_analyze_by_with_ref_level():
    """Test cross_analyze_by with a specified reference level"""
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "A": [10, 20, 30, 40, 50, 60],
            "B": [1, 1, 2, 2, 3, 3],  # Groups: 1, 2, 3
        }
    )

    tree = (
        AnalysisTree()
        .split_by("df.B")
        .cross_analyze_by(ref_lvl="1", mean_diff="np.mean(df.A) - np.mean(ref_df.A)")
    )

    environ = {"np": np}
    result = tree.run(df, environ=environ)

    # The result is a DataTree; check string representation for cross-analysis labels
    result_str = str(result)
    assert "2_vs_1" in result_str
    assert "3_vs_1" in result_str
    # The mean_diff for group 2 vs 1 should be 20 (35 - 15)
    assert "20.0" in result_str


def test_cross_analyze_by_pairwise():
    """Test cross_analyze_by without ref_lvl (pairwise comparisons)"""
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "A": [10, 20, 30, 40, 50, 60],
            "B": [1, 1, 2, 2, 3, 3],  # Groups: 1, 2, 3
        }
    )

    tree = (
        AnalysisTree()
        .split_by("df.B")
        .cross_analyze_by(mean_diff="np.mean(df.A) - np.mean(ref_df.A)")
    )

    environ = {"np": np}
    result = tree.run(df, environ=environ)

    # Should have pairwise comparisons: 2_vs_1, 3_vs_1, 3_vs_2
    result_str = str(result)
    # At minimum, some cross comparisons should exist
    assert "_vs_" in result_str


def test_cross_analyze_by_invalid_ref_level():
    """Test cross_analyze_by raises KeyError with invalid ref_lvl"""
    df = pd.DataFrame(
        {
            "A": [10, 20, 30, 40],
            "B": [1, 1, 2, 2],
        }
    )

    tree = (
        AnalysisTree()
        .split_by("df.B")
        .cross_analyze_by(
            ref_lvl="nonexistent", mean_diff="np.mean(df.A) - np.mean(ref_df.A)"
        )
    )

    environ = {"np": np}
    with pytest.raises(KeyError, match="Reference level 'nonexistent' not found"):
        tree.run(df, environ=environ)


def test_scope_cross_eval():
    """Test scope_cross_eval function"""
    from pyMyriad.utils import scope_cross_eval

    df = pd.DataFrame({"A": [10, 20, 30]})
    ref_df = pd.DataFrame({"A": [5, 10, 15]})

    # Test string expression
    result = scope_cross_eval(
        df=df,
        ref_df=ref_df,
        extra_context={"np": np},
        mean_diff="np.mean(df.A) - np.mean(ref_df.A)",
    )

    assert "mean_diff" in result
    assert result["mean_diff"] == 10.0  # (20) - (10) = 10

    # Test function
    result_func = scope_cross_eval(
        df=df, ref_df=ref_df, sum_diff=lambda df, ref_df: df.A.sum() - ref_df.A.sum()
    )

    assert "sum_diff" in result_func
    assert result_func["sum_diff"] == 30  # (60) - (30) = 30


def test_scope_cross_eval_single_arg_df_callable():
    """Regression test for #60: a single-argument `lambda df: ...` callable -
    valid for analyze_by/scope_eval - must also work in cross_analyze_by,
    dispatched by parameter name instead of being called positionally with
    both df and ref_df.
    """
    from pyMyriad.utils import scope_cross_eval

    df = pd.DataFrame({"A": [10, 20, 30]})
    ref_df = pd.DataFrame({"A": [5, 10, 15]})

    result = scope_cross_eval(df=df, ref_df=ref_df, n=lambda df: len(df))

    assert result == {"n": 3}


def test_scope_cross_eval_single_arg_ref_df_callable():
    """A single-argument `lambda ref_df: ...` callable should also be dispatched
    by name, receiving only ref_df."""
    from pyMyriad.utils import scope_cross_eval

    df = pd.DataFrame({"A": [10, 20, 30]})
    ref_df = pd.DataFrame({"A": [5, 10, 15]})

    result = scope_cross_eval(df=df, ref_df=ref_df, ref_n=lambda ref_df: len(ref_df))

    assert result == {"ref_n": 3}


def test_scope_cross_eval_unrecognized_signature_raises_clear_typeerror():
    """A callable that declares none of df/ref_df/_N should raise a clear,
    actionable TypeError instead of a confusing arity mismatch deep in eval."""
    from pyMyriad.utils import scope_cross_eval

    df = pd.DataFrame({"A": [10, 20, 30]})
    ref_df = pd.DataFrame({"A": [5, 10, 15]})

    with pytest.raises(TypeError, match="bad"):
        scope_cross_eval(df=df, ref_df=ref_df, bad=lambda: 1)


def test_cross_analyze_by_mixes_single_and_two_arg_lambdas():
    """cross_analyze_by should accept a single-arg `lambda df: ...` callable
    (e.g. a plain count) alongside a two-arg `lambda df, ref_df: ...`
    comparison callable in the same call, matching analyze_by's flexibility."""
    df = pd.DataFrame(
        {
            "A": [10, 20, 30, 40, 50, 60],
            "B": [1, 1, 2, 2, 3, 3],
        }
    )

    tree = (
        AnalysisTree()
        .split_by("df.B")
        .cross_analyze_by(
            ref_lvl="1",
            n=lambda df: len(df),
            mean_diff=lambda df, ref_df: np.mean(df.A) - np.mean(ref_df.A),
        )
    )

    result = tree.run(df, environ={"np": np})
    result_str = str(result)
    assert "n: 2" in result_str
    assert "mean_diff: 20.0" in result_str


# --- denom parameter tests ---


def test_analysis_tree_denom_str():
    """AnalysisTree stores denom as self.denom when given a string."""
    tree = AnalysisTree(denom="ID")
    assert tree.denom == "ID"


def test_analysis_tree_denom_list():
    """AnalysisTree stores denom as self.denom when given a list."""
    tree = AnalysisTree(denom=["PatientID", "Visit"])
    assert tree.denom == ["PatientID", "Visit"]


def test_analysis_tree_denom_none():
    """AnalysisTree.denom is None by default."""
    tree = AnalysisTree()
    assert tree.denom is None


def test_analysis_tree_id_deprecated():
    """Passing id= emits DeprecationWarning and sets self.denom."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        tree = AnalysisTree(id="ID")
    assert len(w) == 1
    assert issubclass(w[0].category, DeprecationWarning)
    assert "denom" in str(w[0].message).lower()
    assert tree.denom == "ID"


# multi_simple_analysis


@pytest.fixture
def multi_df():
    """6 subjects x 2 arms, one continuous (AGE) and one categorical (SEX) variable."""
    return pd.DataFrame(
        {
            "USUBJID": ["S1", "S2", "S3", "S4", "S5", "S6"],
            "ARM": ["Placebo", "Placebo", "Placebo", "Active", "Active", "Active"],
            "AGE": [40.0, 45.0, 50.0, 42.0, 47.0, 52.0],
            "SEX": ["Male", "Male", "Female", "Male", "Female", "Female"],
        }
    )


def test_multi_simple_analysis_builds_parallel_branches(multi_df):
    """Regression test for #76: one sibling node per variable, tree reflects the layout.

    A continuous variable becomes a single AnalysisNode; a categorical
    variable becomes a SplitNode (one child per observed level).
    """
    tree = (
        AnalysisTree(denom="USUBJID")
        .split_by("df.ARM", label="Arm")
        .multi_simple_analysis(
            var={"AGE": "continuous", "SEX": "categorical"},
            continuous_fun=["n", "mean"],
            categorical_fun=["n (pct)"],
        )
    )
    arm_node = tree[0]
    assert len(arm_node) == 2
    kinds = {type(n).__name__ for n in arm_node}
    assert kinds == {"AnalysisNode", "SplitNode"}

    age_node = next(n for n in arm_node if getattr(n, "label", None) == "AGE")
    assert isinstance(age_node, AnalysisNode)
    assert set(age_node.analysis) == {"n", "mean"}

    sex_node = next(n for n in arm_node if getattr(n, "label", None) == "SEX")
    assert len(sex_node) == 1  # one AnalysisNode child, split levels come from data


def test_multi_simple_analysis_continuous_values(multi_df):
    """Continuous predefined functions compute correct raw values."""
    tree = (
        AnalysisTree()
        .split_by("df.ARM", label="Arm")
        .multi_simple_analysis(var={"AGE": "continuous"}, continuous_fun=["n", "mean"])
    )
    result = tree.run(multi_df)
    placebo = result["Arm"]["Placebo"]["AGE"]
    assert placebo.summary["n"] == 3
    assert placebo.summary["mean"] == pytest.approx(45.0)


def test_multi_simple_analysis_categorical_percentage(multi_df):
    """Regression test for #76: categorical n (pct) uses denom=/_N for the arm total.

    Placebo arm: SEX = Male, Male, Female -> Male 2/3, Female 1/3.
    """
    tree = (
        AnalysisTree(denom="USUBJID")
        .split_by("df.ARM", label="Arm")
        .multi_simple_analysis(var={"SEX": "categorical"})
    )
    result = tree.run(multi_df)
    male = result["Arm"]["Placebo"]["SEX"]["Male"]["SEX"]
    assert male.summary["n (pct)"] == "2 (67%)"


def test_multi_simple_analysis_categorical_n_no_denom_needed(multi_df):
    """The plain categorical "n" function works without denom= being set."""
    tree = (
        AnalysisTree()
        .split_by("df.ARM", label="Arm")
        .multi_simple_analysis(var={"SEX": "categorical"}, categorical_fun=["n"])
    )
    result = tree.run(multi_df)
    male = result["Arm"]["Placebo"]["SEX"]["Male"]["SEX"]
    assert male.summary["n"] == 2


def test_multi_simple_analysis_n_pct_without_denom_raises():
    """Regression test for #76: "n (pct)" without denom= set fails fast on AnalysisTree."""
    with pytest.raises(ValueError, match="denom"):
        AnalysisTree().split_by("df.ARM", label="Arm").multi_simple_analysis(
            var={"SEX": "categorical"}, categorical_fun=["n (pct)"]
        )


def test_multi_simple_analysis_empty_var_raises():
    """Regression test for #76: an empty `var` dict is rejected up front."""
    with pytest.raises(ValueError):
        AnalysisTree().split_by("df.ARM").multi_simple_analysis(var={})


def test_multi_simple_analysis_unknown_type_raises():
    """An invalid variable type raises a clear ValueError."""
    with pytest.raises(ValueError, match="numeric"):
        AnalysisTree().split_by("df.ARM").multi_simple_analysis(var={"AGE": "numeric"})


def test_multi_simple_analysis_unknown_continuous_fun_raises():
    """An invalid continuous_fun name raises a clear ValueError."""
    with pytest.raises(ValueError, match="average"):
        AnalysisTree().split_by("df.ARM").multi_simple_analysis(
            var={"AGE": "continuous"}, continuous_fun=["average"]
        )


def test_multi_simple_analysis_unknown_categorical_fun_raises():
    """An invalid categorical_fun name raises a clear ValueError."""
    with pytest.raises(ValueError, match="proportion"):
        AnalysisTree(denom="USUBJID").split_by("df.ARM").multi_simple_analysis(
            var={"SEX": "categorical"}, categorical_fun=["proportion"]
        )


def test_multi_simple_analysis_can_follow_terminal_analyze_by(multi_df):
    """Regression test for #76: a prior terminal analyze_by() doesn't block this method.

    Plain split_by() cannot add a sibling split once a terminal analyze_by()
    node exists at a branch; multi_simple_analysis() builds and appends
    nodes directly, so it isn't blocked by that guard.
    """
    tree = (
        AnalysisTree(denom="USUBJID")
        .split_by("df.ARM", label="Arm")
        .analyze_by(existing=lambda df: len(df))
        .multi_simple_analysis(var={"SEX": "categorical"})
    )
    result = tree.run(multi_df)
    arm_node = result["Arm"]["Placebo"]
    assert "SEX" in arm_node
    assert arm_node["0"].summary["existing"] == 3

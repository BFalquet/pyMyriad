
import sys
import pandas as pd
from .data_tree import DataTree, SplitDataNode, LvlDataNode, DataNode
from .utils import scope_eval, get_top_globals

class AnalysisTree(list):
    """A subclass of list that represents an analysis tree with an associated date.

    Args:
        *args: Variable length argument list containing SplitNode or AnalysisNode instances.

    Attributes:
        date (str): The date associated with the analysis tree. Defaults to "Today".
        
    Examples:
        tree = AnalysisTree()
        print(tree)
        analysis tree
        [1, 2, 3]
    """
    def __init__(self, *args):
        """ Initializes the AnalysisTree object.
        Args:
            *args: Variable length argument list containing SplitNode or AnalysisNode instances.
        Raises:
            AssertionError: If any element in args is not an instance of SplitNode or AnalysisNode.
        """

        acceptable_lst = [isinstance(x, (SplitNode, AnalysisNode)) for x in args] 
        assert all(acceptable_lst), "Every element passed to AnalysisTree() must be a SplitNode or an AnalysisNode"

        super().__init__(args)
        self.date = "Today"

    def __str__(self):
        ind = 0
        res = [x.__str__(ind = ind + 2) for x in self]
        recusive_str = "".join(res)
        return "Analysis Tree\n" + recusive_str
    
    def run(self, data: pd.DataFrame, environ: dict = None) -> DataTree:
        """Run the analysis tree on the provided DataFrame.
        Args:
            data (pd.DataFrame): The DataFrame to analyze.
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
        Returns:
            DataTree: The resulting DataTree after running the analysis tree.
        Examples:
            a_node = AnalysisNode(m = "1", s = "2") # no eval in analysis
            s_node = SplitNode(a_node, a_node, expr = "df.B > 50")
            a_tree = AnalysisTree(s_node, a_node)
            df = pd.DataFrame({
                "A": [10, 11, 12, 14, 15, 16],
                "B": [10, 20, 40 ,50 ,60, 100]
            })
            res = a_tree.run(df)
        """
        
        if environ is None:
            environ = get_top_globals()

        # Recursively apply run.
        res_lst = [elements.run(data, environ = environ) for elements in self]
        
        res_names = []
        for x in res_lst:
            if isinstance(x, SplitDataNode):
                res_names.append(x.split_var or "Custom Split")
            else:
                res_names.append(x.label or "Custom")
        
        res = dict(zip(res_names, res_lst))
        return DataTree(**res)

class SplitNode(list):
    """A subclass of list representing a splitting node.
    Attributes:
        expr (str): The expression describing how data should be split.
        kwexpr (dict): A dictionary with the name of the group and the associated expression
            describing how they should be split.
    """
    def __init__(self, *args, expr:str = None, **kwargs) -> None:
        """
        Initializes the SplitNode object.
        Args:
            *args: Additional positional arguments.
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Raises:
            AssertionError: If neither `expr` nor `kwargs` are provided, or if both are provided.
        Returns:
            None
        Examples:
            SplitNode("age > 50")
            SplitNode(Y = "age > 50", N = "age <= 50")
        """

        super().__init__(args)

        if expr is None:
            self.expr = None
            assert len(kwargs) != 0, "Either expr or kwargs must be provided."
            self.kwexpr = kwargs
        else:
            self.expr = expr
            assert len(kwargs) == 0, "Either expr or kwargs must be provided. Not both."
            self.kwexpr = None

    def __str__(self, ind: int = 0):
        if self.expr is not None:
            res = self.expr + "\n"
        else:
            expr_lst = [f"{i}: {self.kwexpr[i]} " for i in self.kwexpr.keys()]
            res = "".join(expr_lst) + "\n"

        split_str = (" " * ind) + "Split Node:\n" + (" " * ind) + " |-- " + res
        recusive_lst = [x.__str__(ind = ind + 2) for x in self]
        recusive_str = "".join(recusive_lst)

        return split_str + recusive_str
    
    def run(self, data: pd.DataFrame, environ: dict = None) -> SplitDataNode:
        """Run the split node on the provided DataFrame.
        Args:
            data (pd.DataFrame): The DataFrame to split.
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
        Returns:
            SplitDataNode: The resulting SplitDataNode after running the split node.
        Examples:
            a_node = AnalysisNode(m = "1", s = "2") # no eval in analysis
            s_node = SplitNode(a_node, a_node, expr = "df.B > 50")
            a_tree = AnalysisTree(s_node, a_node)
            df = pd.DataFrame({
                "A": [10, 11, 12, 14, 15, 16],
                "B": [10, 20, 40 ,50 ,60, 100]
            })
            res = a_tree.run(df)
        """

        if self.expr is not None:
            # Split using a single expression.
            gp_eval_dict = scope_eval(df = data, extra_context = environ, **{"gp": self.expr})
            gp_bool = gp_eval_dict["gp"]

            groups = data.groupby(gp_bool)
                # data.eval(self.expr, **(environ or {}))
                
            # Convert to dictionary of DataFrames
            split_dfs = {str(name): group for name, group in groups}

        else:
            # Split using multiple expressions.
            # Note: Group might not cover all rows or overlap.
            split_dfs = {}
            gp_eval_dict = scope_eval(df = data, extra_context = environ, **self.kwexpr)
            for n, gp in gp_eval_dict.items():
                split_dfs.update({n: data[gp]})

        # Recursively apply run for each data frame (that now contain the name of the groups), 
        # create a lvlnode which contains the rest of the tree
        # the self of the lvl node is the rest of the tree on which run has been applied
        res_dic = {n: LvlDataNode(split_lvl = str(n), **{str(nn): element.run(data, environ = environ) for nn, element in enumerate(self)}) for n, data in split_dfs.items()}
        
        split_var = self.expr or "::".join(self.kwexpr.keys())

        return SplitDataNode(split_var = split_var, **res_dic)

class AnalysisNode():
    """A class representing how data should be analyzed.
    
    Attributes:
        analysis (dict): A dictionary with keys as the names of the analyses and values as the expressions.
        label (str): The analysis label.
        termination (bool): Whether this node is a termination node.
    """

    def __init__(self, *args, label: str = str(), termination: bool = True, **kwargs):
        """Initializes the AnalysisNode object.
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to True.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.
        Raises:
            AssertionError: If no analysis expressions are provided.
        Returns:    
            None
        Examples:
            AnalysisNode(m = "np.mean(df.A)", s = "np.std(df.B)")
            AnalysisNode("np.mean(df.A)", "np.std(df.B)", label = "Summary Stats") 
            AnalysisNode("np.mean(df.A)", "np.std(df.B)", label = "Summary Stats", termination = False)
        """

        analysis = {k: k for k in args} | kwargs
        assert len(analysis) > 0, "At least one analyis must be provided"

        self.analysis = analysis
        self.label = label
        self.termination = termination

    def __str__(self, ind: int = 0):
        analysis_lst = [f"{(ind + 4) * ' '}{i}: {self.analysis[i]}\n" for i in self.analysis.keys()]
        analysis_str = (" " * (ind + 2)) + f"Analysis Node: {self.label}\n" + "". join(analysis_lst)
        return analysis_str
    
    def run(self, data, environ = None) -> DataNode:
        """Run the analysis node on the provided DataFrame.
        Args:
            data (pd.DataFrame): The DataFrame to analyze.
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
        Returns:
            DataNode: The resulting DataNode after running the analysis node.
        Examples:
            import numpy as np
            a_node = AnalysisNode(m = "np.mean(df.A)", s = "np.std(df.B)")
            df = pd.DataFrame({
                "A": [10, 20],
                "B": [10, 10]
            })
            
            res = a_node.run(df, environ = environ)
            assert res.summary == {"m": np.float64(15), "s": np.float64(0)}
        """

        res = scope_eval(df = data, extra_context = environ, **self.analysis)
        return DataNode(data = data, summary = res, label = self.label, depth = 0)

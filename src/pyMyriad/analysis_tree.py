
import sys
import inspect
import ast
import pandas as pd
from .data_tree import DataTree, SplitDataNode, LvlDataNode, DataNode
from .utils import scope_eval, get_top_globals

#region AnalysisTree

class AnalysisTree(list):
    """A subclass of list that represents an analysis tree.
    Args:
        *args: Variable length argument list containing SplitNode or AnalysisNode instances.
    Attributes:
        att (any): additional attributes can be added here.
    Examples:
        tree = AnalysisTree()
        print(tree)
    """
    def __init__(self, *args, id:str = None):
        """ Initializes the AnalysisTree object.
        Args:
            *args: Variable length argument list containing SplitNode or AnalysisNode instances.
            id (str, optional): The name of the column whose unique counts identifies the number of entities. Defaults to None.
        Raises:
            AssertionError: If any element in args is not an instance of SplitNode or AnalysisNode.
        """

        acceptable_lst = [isinstance(x, (SplitNode, AnalysisNode)) for x in args] 
        assert all(acceptable_lst), "Every element passed to AnalysisTree() must be a SplitNode or an AnalysisNode"

        super().__init__(args)
        self.att = ()
        self.id = id

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

        _N = count_or_length(data, self.id)

        # Recursively apply run.
        res_lst = [elements.run(data, environ = environ, id = self.id) for elements in self]
        
        res_names = []
        for x in res_lst:
            if isinstance(x, SplitDataNode):
                res_names.append(x.split_var or "Custom Split")
            else:
                res_names.append(x.label or "Custom")
        
        res = dict(zip(res_names, res_lst))
        return DataTree(_N = _N, **res)
    
    def split_by(self, expr: str = None, label: str = None, **kwargs):
        """Add a split node at the extremites of the branches.
        Note: 
            No split node is added where there is already a split node or an analysis node with termination signal.
        Args:
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added.
        Examples:
            a_tree = AnalysisTree()
            a_tree = a_tree.split_by(m = "df.A > 50")
            a_tree = a_tree.split_by("df.B > 50")
        """
        
        is_split_node = [isinstance(x, SplitNode) for x in self]
        no_termination = not any([x.termination for x in self if isinstance(x, AnalysisNode)])

        # length 0 OR (no split node and no termination signal)
        if ((len(is_split_node) == 0) or ((not any(is_split_node)) and no_termination)):
            self.append(SplitNode(expr = expr, label = label, **kwargs))
        
        else:
            for i in range(len(self)):
                    if isinstance(self[i], SplitNode):
                        self[i] = self[i].split_by(expr = expr, label = label, **kwargs)
                
        return self
    
    def split_at_by(self, path: list, expr: str = None, label:str = None, **kwargs):
        """Add a split node at a specific path in the tree.
        
        Args:
            path (list): A list representing the path where the split node should be added.
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added at the specified path.
        Examples:
            a_tree = AnalysisTree()
            a_tree = a_tree.split_at_by(["M", "Benin"], m = "df.A > 50")
        """
        
        if (len(path) == 0):
            self.append(SplitNode(expr = expr, label = label, **kwargs))

        else:
            for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    if (self[i].label == path[0]) or (path[0] == "*"):
                        self[i] = self[i].split_at_by(path = path[1:], expr = expr, label = label, **kwargs)
        
        return self
    
    def split_at_root_by(self, expr: str = None, label:str = None, **kwargs):
        """Add a split node at the root of the tree."""
        self.append(SplitNode(expr = expr, label = label, **kwargs))
    
    def analyze_by(self, *args, label: str = str(), termination: bool = True, **kwargs):
        """Add an analyis node at the extremites of the branches.
        
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to True.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new analysis node added.
        Examples:
            a_tree = AnalysisTree()
            a_tree = a_tree.analyze_by(m = "np.mean(A)", s = "np.std(B)")
            a_tree = a_tree.analyze_by("np.mean(A)", "np.std(B)", label = "Summary Stats")
        """
        is_split_node = [isinstance(x, SplitNode) for x in self]

        # length 0 OR (no split node and no termination signal)
        if ((len(is_split_node) == 0) or (not any(is_split_node))):
            self.append(AnalysisNode(*args, label = label, termination = termination, **kwargs))
        
        else:
            for i in range(len(self)):
                    if isinstance(self[i], SplitNode):
                        self[i] = self[i].analyze_by(*args, label = label, termination = termination, **kwargs)

        return self
    
    def analyze_by_at(self, path: list, *args, label: str = str(), termination: bool = True, **kwargs):
        """Add an analysis node at a specific path in the tree."""
        if (len(path) == 0):
            self.append(AnalysisNode(*args, label = label, termination = termination, **kwargs))
        else:
            for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    if (self[i].label == path[0]) or (path[0] == "*"):
                        self[i] = self[i].analyze_by_at(path = path[1:], *args, label = label, termination = termination, **kwargs)

        return self

    def summarize_by(self, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at the extremities of the branches."""
        self.analyze_by(*args, label = label, termination = termination, **kwargs)
        return self
    
    def summarize_by_at(self, path: list, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at a specific path in the tree."""
        self.analyze_by_at(path = path, *args, label = label, termination = termination, **kwargs)
        return self


#endregion

#region SplitNode

class SplitNode(list):
    """A subclass of list representing a splitting node.
    Attributes:
        expr (str): The expression describing how data should be split.
        label (str): The label of the node. By default the `expr` or the keys of `kwargs`.
        kwexpr (dict): A dictionary with the name of the group and the associated expression
            describing how they should be split.
    """
    def __init__(self, *args, expr:str = None, label:str = None, **kwargs) -> None:
        """
        Initializes the SplitNode object.
        Args:
            *args: Additional positional arguments.
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
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
            self.label = label or "-".join(kwargs.keys())
            self.str = {k: analysis_to_string(v) for k, v in kwargs.items()}
        else:
            self.expr = expr
            assert len(kwargs) == 0, "Either expr or kwargs must be provided. Not both."
            self.kwexpr = None
            self.label = label or expr
            self.str = analysis_to_string(expr)

    def __str__(self, ind: int = 0):
        if self.expr is not None:
            res = self.str
        else:
            expr_lst = [f"{k}: {v}" for k,v in self.str.items()]
            res = " -- ".join(expr_lst)

        split_str = (" " * ind) + f"└- Split Node {self.label}: [" + res + "]\n"
        recusive_lst = [x.__str__(ind = ind + 2) for x in self]
        recusive_str = "".join(recusive_lst)

        return split_str + recusive_str

    def run(self, data: pd.DataFrame, environ: dict = None, id: str = None, _N: int = None) -> SplitDataNode:
        """Run the split node on the provided DataFrame.
        Args:
            data (pd.DataFrame): The DataFrame to split.
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
            id (str, optional): The name of the column whose unique counts identifies the number of entities. Defaults to None.
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
                
            # Convert to dictionary of DataFrames
            split_dfs = {str(name): group for name, group in groups}

        else:
            # Split using multiple expressions.
            # Note: Group might overlap or not cover all rows.
            split_dfs = {}
            gp_eval_dict = scope_eval(df = data, extra_context = environ, **self.kwexpr)
            for n, gp in gp_eval_dict.items():
                split_dfs.update({n: data[gp]})

        # Recursively apply run for each data frame (that now contain the name of the groups), 
        # create a lvlnode which contains the rest of the tree
        # the self of the lvl node is the rest of the tree on which run has been applied
        res_dic = {str(n): LvlDataNode(split_lvl = str(n), _N = count_or_length(data, id), **{str(nn): element.run(data, environ = environ, id = id, _N = None) for nn, element in enumerate(self)}) for n, data in split_dfs.items()}
        
        print(res_dic.keys())

        split_var = self.expr or "::".join(self.kwexpr.keys())

        return SplitDataNode(split_var = split_var, label = self.label, **res_dic)
    
    def split_by(self, expr: str = None, label:str = None, **kwargs):
        """Add a split node at the extremites of the branches.

        Note: 
            No split node is added where there is already a split node or an analysis node with termination signal.
        Args:
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added.
        Examples:
            a_tree = AnalysisTree()
            a_tree = a_tree.split_by(m = "A > 50")
            a_tree = a_tree.split_by("B > 50")
        """
            
        is_split_node = [isinstance(x, SplitNode) for x in self]
        no_termination = not any([x.termination for x in self if isinstance(x, AnalysisNode)])
        
        # length 0 OR (no split node and no termination signal)
        if ((len(is_split_node) == 0) or ((not any(is_split_node)) and no_termination)):
            self.append(SplitNode(expr = expr, label = label, **kwargs))
        
        else:
            for i in range(len(self)):
                    if isinstance(self[i], SplitNode):
                        self[i] = self[i].split_by(expr = expr, label = label, **kwargs)
                
        return self
    
    def split_at_by(self, path: list, expr: str = None, label:str = None, **kwargs):
        """Add a split node at a specific path in the tree.
        
        Args:
            path (list): A list representing the path where the split node should be added.
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added at the specified path.
        Examples:
            a_tree = AnalysisTree()
            a_tree = a_tree.split_at_by(["M", "Benin"], m = "df.A > 50")
        """
        
        if (len(path) == 0):
            self.append(SplitNode(expr = expr, label = label, **kwargs))

        else:
            for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    if (self[i].label == path[0]) or (path[0] == "*"):
                        self[i] = self[i].split_at_by(path = path[1:], expr = expr, label = label, **kwargs)
        
        return self
    
    def analyze_by(self, *args, label: str = str(), termination: bool = True, **kwargs):
        """Add an analyis node at the extremites of the branches.
        
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to True.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new analysis node added.
        Examples:
            a_tree = AnalysisTree()
            a_tree = a_tree.analyze_by(m = "np.mean(A)", s = "np.std(B)")
            a_tree = a_tree.analyze_by("np.mean(A)", "np.std(B)", label = "Summary Stats")
        """
        is_split_node = [isinstance(x, SplitNode) for x in self]

        # length 0 OR (no split node and no termination signal)
        if ((len(is_split_node) == 0) or (not any(is_split_node))):
            self.append(AnalysisNode(*args, label = label, termination = termination, **kwargs))
        
        else:
            for i in range(len(self)):
                    if isinstance(self[i], SplitNode):
                        self[i] = self[i].analyze_by(*args, label = label, termination = termination, **kwargs)

        return self
    
    def analyze_by_at(self, path: list, *args, label: str = str(), termination: bool = True, **kwargs):
        """Add an analysis node at a specific path in the tree."""
        if (len(path) == 0):
            self.append(AnalysisNode(*args, label = label, termination = termination, **kwargs))
        else:
            for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    if (self[i].label == path[0]) or (path[0] == "*"):
                        self[i] = self[i].analyze_by_at(path = path[1:], *args, label = label, termination = termination, **kwargs)

        return self
    
    def summarize_by(self, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at the extremites of the branches."""

        self.analyze_by(*args, label = label, termination = termination, **kwargs)
        return self

    def summarize_by_at(self, path: list, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at a specific path in the tree."""
        self.analyze_by_at(path = path, *args, label = label, termination = termination, **kwargs)
        return self

#endregion

#region AnalysisNode

class AnalysisNode():
    """A class representing how data should be analyzed.
    
    Attributes:
        analysis (dict): A dictionary with keys as the names of the analyses and values as the expressions.
        analysis_str (str): A string representation of the analysis expressions.
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
         
        # take the first element of analysis
        self.analysis_str = {k: analysis_to_string(v) for k,v in analysis.items()}
        self.label = label
        self.termination = termination

    def __str__(self, ind: int = 0):
        analysis_lst = [f"{(ind + 6) * ' '}{i}: {j}\n" for i,j in self.analysis_str.items()]
        analysis_str = (" " * (ind + 2)) + f"└- Analysis Node: {self.label}\n" + "". join(analysis_lst)
        return analysis_str
    
    def run(self, data, environ = None, id: str = None, _N:int = None) -> DataNode:
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
        return DataNode(data = data, summary = res, label = self.label, depth = 0, _N = _N)

#endregion

def analysis_to_string(analysis):
    """Convert an analysis expression to a string representation.
    
    Args:
        analysis (str or function): The analysis expression, either as a string or a function.
    Returns:
        str: The string representation of the analysis expression.
    Examples:
        mfun = lambda df: np.mean(df.Income)
        analysis_to_string(mfun)  # Returns: "lambda df: np.mean(df.Income)"
    """
    if callable(analysis):
        try:
            source = inspect.getsourcelines(analysis)[0][0].strip()
            # Parse and extract just the lambda expression
            tree = ast.parse(source)
            return ast.get_source_segment(source, tree.body[0]).strip()
        except Exception as e:
            print(f"function {analysis.__name__}")
    return str(analysis)

def count_or_length(data: pd.DataFrame, id: str) -> int:
    """Count the number of unique entities in the DataFrame based on the specified id column.
    
    Args:
        data (pd.DataFrame): The DataFrame to analyze.
        id (str): The name of the column whose unique counts identifies the number of entities.
    Returns:
        int: The number of unique entities in the DataFrame.
    Examples:
        df = pd.DataFrame({
            "id": [1, 2, 1, 3],
            "value": [10, 20, 10, 30]
        })
        count_or_length(df, "id")  # Returns: 3
    """
    if id is None:
        return len(data)
    else:
        return data[id].nunique()

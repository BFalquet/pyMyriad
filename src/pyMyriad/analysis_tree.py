
import sys
import inspect
import ast
import pandas as pd
from .data_tree import DataTree, SplitDataNode, LvlDataNode, DataNode
from .utils import scope_eval, get_top_globals, analysis_to_string, count_or_length, scope_cross_eval

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
    
    Note:
        For string expressions like "np.mean(df.A)", numpy and pandas are auto-injected 
        as 'np' and 'pd'. To avoid warnings, use lambda functions instead:
        `analyze_by(mean_a=lambda df: np.mean(df.A))`
        
        Or explicitly set the environment:
        `AnalysisTree.set_default_environ({'np': np, 'pd': pd})`
    """
    
    # Class-level default environment for expression evaluation
    _default_environ = None
    
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
            if AnalysisTree._default_environ is not None:
                environ = AnalysisTree._default_environ.copy()
            else:
                environ = get_top_globals()

        _N = count_or_length(data, self.id)

        # Recursively apply run.
        res_lst = [elements.run(data, environ = environ, id = self.id) for elements in self]
        
        res_names = []
        for x in res_lst:
            if isinstance(x, SplitDataNode):
                res_names.append(x.label or "Custom Split")
            else:
                res_names.append(x.label or "Custom")
        
        res = dict(zip(res_names, res_lst))
        
        # TODO: hande case where res_name is not a string.

        return DataTree(_N = _N, **res)
    
    @classmethod
    def set_default_environ(cls, environ: dict = None):
        """Set a class-level default environment for expression evaluation.
        
        This allows you to configure imports once instead of passing environ
        to every run() call. When set, this environment is used as the default
        for all AnalysisTree instances.
        
        Args:
            environ (dict, optional): A dictionary mapping names to modules/values.
                Pass None to clear the default and revert to auto-detection.
        
        Examples:
            import numpy as np
            import pandas as pd
            
            # Set default imports once
            AnalysisTree.set_default_environ({'np': np, 'pd': pd})
            
            # Now all trees will use these imports without warnings
            tree = AnalysisTree().split_by("df.Gender").analyze_by(mean="np.mean(df.Income)")
            result = tree.run(df)  # No need to pass environ
            
            # Clear the default
            AnalysisTree.set_default_environ(None)
        """
        cls._default_environ = environ
    
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

        return self
    
    def analyze_by(self, *args, label: str = str(), termination: bool = True, **kwargs):
        """Add an analysis node at the extremites of the branches.
        
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
    
    def analyze_at_by(self, path: list, *args, label: str = str(), termination: bool = True, **kwargs):
        """Add an analysis node at a specific path in the tree."""
        if (len(path) == 0):
            self.append(AnalysisNode(*args, label = label, termination = termination, **kwargs))
        else:
            for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    if (self[i].label == path[0]) or (path[0] == "*"):
                        self[i] = self[i].analyze_at_by(path = path[1:], *args, label = label, termination = termination, **kwargs)

        return self

    def summarize_by(self, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at the extremities of the branches."""
        self.analyze_by(*args, label = label, termination = termination, **kwargs)
        return self
    
    def summarize_at_by(self, path: list, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at a specific path in the tree."""
        self.analyze_at_by(path = path, *args, label = label, termination = termination, **kwargs)
        return self
    
    def cross_analyze_by(self, *args, label: str = str(), ref_lvl: str = str(), termination: bool = True, **kwargs):
        """Add a cross-analysis node at the extremites of the branches.
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            ref_lvl (str, optional): The reference level for comparison. Defaults to an empty string, which lead to comparing every level with each other.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to True.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.

        Returns:
            AnalysisTree: The modified AnalysisTree with the new cross-analysis node added.
        Examples:
            a_tree = AnalysisTree()
            a_tree.split_by(m = "df.A > 50")
            a_tree = a_tree.cross_analyze_by(m = "np.mean(df.A) - np.mean(ref_df.A)", s = "np.median(df.B) - np.median(ref_df.B)")
        """

        for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    self[i] = self[i].cross_analyze_by(*args, label = label, ref_lvl = ref_lvl, termination = termination, **kwargs)

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
            self.label = label or analysis_to_string(expr)
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
        # res_dic = {str(n): LvlDataNode(split_lvl = str(n), _N = count_or_length(data, id), **{str(nn): element.run(data, environ = environ, id = id, _N = None) for nn, element in enumerate(self)}) for n, data in split_dfs.items()}

        # Selectt the elements of self that are not CrossAnalysisNode

        not_cross_analysis_node = {nn: element for nn, element in enumerate(self) if not isinstance(element, CrossAnalysisNode)}
        cross_analysis_node = {nn: element for nn, element in enumerate(self) if isinstance(element, CrossAnalysisNode)}

        res_dic = {str(n): LvlDataNode(split_lvl = str(n), _N = count_or_length(data, id), **{(str(element.label) or str(nn)): element.run(data, environ = environ, id = id, _N = None) for nn, element in not_cross_analysis_node.items()}) for n, data in split_dfs.items()}

        # Handle CrossAnalysisNode separately
        if (len(cross_analysis_node) > 0) and (len(split_dfs) > 1):
            for nn, element in cross_analysis_node.items():
                # Create pairwise combinations to reference levels by selecting data frames from split_dfs
                ref_lvl = element.ref_lvl

                # If a reference level is specified, compare every level to the reference level.
                if len(ref_lvl) > 0:
                    # Validate that the reference level exists
                    if ref_lvl not in split_dfs:
                        raise KeyError(f"Reference level '{ref_lvl}' not found in split levels: {list(split_dfs.keys())}")
                    
                    ref_df = split_dfs[ref_lvl]
                    non_ref_lvls = set(split_dfs.keys()) - {ref_lvl}
                    
                    for var_lvl in non_ref_lvls:
                        var_df = split_dfs[var_lvl]
                        cross_data = { "df": var_df, "ref_df": ref_df }
                        cross_label = f"{var_lvl}_vs_{ref_lvl}"
                        res_dic[cross_label] = LvlDataNode(split_lvl = cross_label, _N = count_or_length(var_df, id), **{(str(element.label) or str(nn)): element.run(cross_data, environ = environ, id = id, _N = None) for nn, element in cross_analysis_node.items()})
                
                # If no reference level is specified, compare every level with each other.
                else:
                    df_keys = list(split_dfs.keys())
                    for ref_lvl_i in range(len(df_keys) - 1):
                        ref_df = split_dfs[df_keys[ref_lvl_i]]
                        for var_lvl_i in range(ref_lvl_i + 1, len(df_keys)):
                            var_df = split_dfs[df_keys[var_lvl_i]]
                            cross_data = { "df": var_df, "ref_df": ref_df }
                            cross_label = f"{df_keys[var_lvl_i]}_vs_{df_keys[ref_lvl_i]}"
                            res_dic[cross_label] = LvlDataNode(split_lvl = cross_label, _N = count_or_length(var_df, id), **{(str(element.label) or str(nn)): element.run(cross_data, environ = environ, id = id, _N = None) for nn, element in cross_analysis_node.items()})


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
        """Add an analysis node at the extremites of the branches.
        
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
    
    def analyze_at_by(self, path: list, *args, label: str = str(), termination: bool = True, **kwargs):
        """Add an analysis node at a specific path in the tree."""
        if (len(path) == 0):
            self.append(AnalysisNode(*args, label = label, termination = termination, **kwargs))
        else:
            for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    if (self[i].label == path[0]) or (path[0] == "*"):
                        self[i] = self[i].analyze_at_by(path = path[1:], *args, label = label, termination = termination, **kwargs)

        return self
    
    def summarize_by(self, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at the extremites of the branches."""

        self.analyze_by(*args, label = label, termination = termination, **kwargs)
        return self

    def summarize_at_by(self, path: list, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at a specific path in the tree."""
        self.analyze_at_by(path = path, *args, label = label, termination = termination, **kwargs)
        return self
    
    def cross_analyze_by(self, *args, label: str = str(), ref_lvl: str = str(), termination: bool = True, **kwargs):
        """Add a cross-analysis node at the extremites of the branches.
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            ref_lvl (str, optional): The reference level for comparison. Defaults to an empty string, which lead to comparing every level with each other.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to True.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.

        Returns:
            AnalysisTree: The modified AnalysisTree with the new cross-analysis node added.
        Examples:
            a_tree = AnalysisTree()
            a_tree.split_by(m = "df.A > 50")
            a_tree = a_tree.cross_analyze_by(m = "np.mean(df.A) - np.mean(ref_df.A)", s = "np.median(df.B) - np.median(ref_df.B)")
        """
        is_split_node = [isinstance(x, SplitNode) for x in self]
        # length 0 OR (no split node and no termination signal)
        if ((len(is_split_node) == 0) or (not any(is_split_node))):
            self.append(CrossAnalysisNode(*args, label = label, ref_lvl = ref_lvl, termination = termination, **kwargs))

        else:
            for i in range(len(self)):
                    if isinstance(self[i], SplitNode):
                        self[i] = self[i].cross_analyze_by(*args, label = label, ref_lvl = ref_lvl, termination = termination, **kwargs)

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
        assert len(analysis) > 0, "At least one analysis must be provided"

        self.analysis = analysis
         
        # take the first element of analysis
        self.analysis_str = {k: analysis_to_string(v) for k,v in analysis.items()}
        self.label = label
        self.termination = termination

    def __str__(self, ind: int = 0):
        analysis_lst = [f"{(ind + 4) * ' '}{i}: {j}\n" for i,j in self.analysis_str.items()]
        analysis_str = (" " * (ind + 0)) + f"└- Analysis Node: {self.label}\n" + "". join(analysis_lst)
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

#region CrossAnalysisNode

class CrossAnalysisNode(list):
    """A class representing how data should be cross-analyzed.
    
    Attributes:
        analysis (dict): A dictionary with keys as the names of the analyses and values as the expressions.
        analysis_str (str): A string representation of the analysis expressions.
        label (str): The analysis label.
        ref_lvl (str): The reference level for comparison.
        termination (bool): Whether this node is a termination node.
    """

    def __init__(self, *args, label: str = str(), ref_lvl: str = str(), termination: bool = True, **kwargs):
        """Initializes the CrossAnalysisNode object.
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            ref_lvl (str, optional): The reference level for comparison. Defaults to an empty string, which lead to comparing every level with each other.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to True.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.
        Raises:
            AssertionError: If no analysis expressions are provided.
        Returns:    
            None

        Examples:
            CrossAnalysisNode("np.mean(df1.A) - np.mean(df2.A)", "np.median(df1.B) - np.median(df2.B)", label = "Summary Stats") 
        """

        analysis = {k: k for k in args} | kwargs
        assert len(analysis) > 0, "At least one analysis must be provided"

        super().__init__(args)

        self.analysis = analysis
         
        # take the first element of analysis
        self.analysis_str = {k: analysis_to_string(v) for k,v in analysis.items()}
        self.label = label
        self.ref_lvl = ref_lvl
        self.termination = termination

    def __str__(self, ind: int = 0):
        analysis_lst = [f"{(ind + 4) * ' '}{i}: {j}\n" for i,j in self.analysis_str.items()]
        analysis_str = (" " * (ind + 0)) + f"└- Cross Analysis Node: {self.label}\n" + "". join(analysis_lst)
        return analysis_str
    
    def run(self, data: dict, environ = None, id: str = None, _N:int = None) -> DataNode:
        """Run the cross-analysis node on the provided DataFrames.
        Args:
            data (dict): A dictionary containing two DataFrames to analyze. Keys should be "df" and "ref_df".
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
        Returns:
            DataNode: The resulting DataNode after running the cross-analysis node.
        """

        res = scope_cross_eval(df = data["df"], ref_df = data["ref_df"], extra_context = environ, **self.analysis)
        return DataNode(data = data["df"], summary = res, label = self.label, depth = 0, _N = _N) # TODO: do we need another class for cross data node?
    

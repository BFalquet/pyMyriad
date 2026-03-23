"""Analysis tree construction module.

This module provides classes for building hierarchical analysis trees that define
analytical workflows. Analysis trees specify how data should be split (stratified)
and what analyses should be performed on each group.

The main classes are:
- AnalysisTree: The root container for an analysis tree
- SplitNode: Defines how to split/stratify data
- AnalysisNode: Defines what computations to perform
- CrossAnalysisNode: Defines comparisons between groups

Typical workflow:
    1. Create an AnalysisTree
    2. Add splits using split_by() or split_at_by()
    3. Add analyses using analyze_by() or analyze_at_by()
    4. Run the tree on data to get a DataTree with results

Example:
    >>> tree = AnalysisTree()
    >>> tree = tree.split_by('df.Gender')
    >>> tree = tree.analyze_by(mean=lambda df: np.mean(df.Income))
    >>> result = tree.run(df)

See also:
    - ARCHITECTURE.md: Detailed architectural overview
    - examples/EXAMPLES_GUIDE.md: Usage patterns and examples
    - data_tree.py: Result data structures
"""

import json
import os
import warnings
import pandas as pd
from .data_tree import DataTree, SplitDataNode, LvlDataNode, DataNode
from .utils import scope_eval, get_top_globals, analysis_to_string, count_or_length, scope_cross_eval, _callable_to_expr_str

#region AnalysisTree

class AnalysisTree(list):
    """A subclass of list that represents an analysis tree.
    Args:
        *args: Variable length argument list containing SplitNode or AnalysisNode instances.
    Attributes:
        att (any): additional attributes can be added here.
    Examples:
        >>> tree = AnalysisTree()
        >>> print(tree)
    
    Note:
        For string expressions like "np.mean(df.A)", numpy and pandas are auto-injected 
        as 'np' and 'pd'. To avoid warnings, use lambda functions instead:
        `analyze_by(mean_a=lambda df: np.mean(df.A))`
        
        Or explicitly set the environment:
        `AnalysisTree.set_default_environ({'np': np, 'pd': pd})`
    """
    
    # Class-level default environment for expression evaluation
    _default_environ = None
    
    def __init__(self, *args, denom: str | list[str] | None = None, id: str = None):
        """ Initializes the AnalysisTree object.
        Args:
            *args: Variable length argument list containing SplitNode or AnalysisNode instances.
            denom (str or list of str, optional): The column name(s) used to count unique
                observations at each level of the tree. When set, analysis expressions receive
                ``_N`` — a list of cumulative unique counts from root to the current level.
                If a list of column names is provided, unique row combinations are counted.
                Defaults to None.
            id (str, optional): Deprecated. Use ``denom`` instead.
        Raises:
            AssertionError: If any element in args is not an instance of SplitNode or AnalysisNode.
        """

        acceptable_lst = [isinstance(x, (SplitNode, AnalysisNode)) for x in args] 
        assert all(acceptable_lst), "Every element passed to AnalysisTree() must be a SplitNode or an AnalysisNode"

        if id is not None and denom is None:
            warnings.warn(
                "The 'id' parameter is deprecated. Use 'denom' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            denom = id

        super().__init__(args)
        self.att = ()
        self.denom = denom

    def __str__(self):
        """Return a string representation of the analysis tree.
        
        Returns:
            str: Formatted tree structure showing splits and analyses.
        """
        if len(self) == 0:
            return "Analysis Tree\n"
        
        result = ["Analysis Tree\n"]
        for i, node in enumerate(self):
            is_last = (i == len(self) - 1)
            result.append(node.__str__(is_last=is_last, prefix=""))
        return "".join(result)

    def run(self, data: pd.DataFrame, environ: dict = None) -> DataTree:
        """Run the analysis tree on the provided DataFrame.
        Args:
            data (pd.DataFrame): The DataFrame to analyze.
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
        Returns:
            DataTree: The resulting DataTree after running the analysis tree.
        Examples:
            >>> a_node = AnalysisNode(m = "1", s = "2")  # no eval in analysis
            >>> s_node = SplitNode(a_node, a_node, expr = "df.B > 50")
            >>> a_tree = AnalysisTree(s_node, a_node)
            >>> df = pd.DataFrame({
            ...     "A": [10, 11, 12, 14, 15, 16],
            ...     "B": [10, 20, 40 ,50 ,60, 100]
            ... })
            >>> res = a_tree.run(df)
        """
        
        if environ is None:
            if AnalysisTree._default_environ is not None:
                environ = AnalysisTree._default_environ.copy()
            else:
                environ = get_top_globals()

        _N = [count_or_length(data, self.denom)] if self.denom is not None else None

        # Recursively apply run.
        res_lst = [elements.run(data, environ = environ, denom = self.denom, _N = _N) for elements in self]
        
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
            >>> import numpy as np
            >>> import pandas as pd
            
            # Set default imports once
            >>> AnalysisTree.set_default_environ({'np': np, 'pd': pd})
            
            # Now all trees will use these imports without warnings
            >>> tree = AnalysisTree().split_by("df.Gender").analyze_by(mean="np.mean(df.Income)")
            >>> result = tree.run(df)  # No need to pass environ
            
            # Clear the default
            >>> AnalysisTree.set_default_environ(None)
        """
        cls._default_environ = environ

    # -------------------------------------------------------------------------
    # JSON serialization / deserialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the analysis tree to a JSON-compatible dictionary.

        The dictionary captures the full tree structure including all split
        and analysis expressions, labels, and the ``denom`` setting.
        Callable (lambda) expressions are converted to their body string so the
        result is fully JSON-serializable.  Pass the output to
        :meth:`from_dict` to reconstruct an equivalent tree.

        Returns:
            dict: A JSON-serializable representation of the tree.

        See Also:
            to_json : Serialize to a JSON string (optionally writing to a file).
            from_dict : Reconstruct a tree from a dictionary.

        Examples:
            >>> import numpy as np
            >>> tree = (AnalysisTree()
            ...     .split_by("df.Gender")
            ...     .analyze_by(mean=lambda df: np.mean(df.Income)))
            >>> d = tree.to_dict()
            >>> d["type"]
            'AnalysisTree'
            >>> d["nodes"][0]["type"]
            'SplitNode'
        """
        return {
            "type": "AnalysisTree",
            "denom": self.denom,
            "nodes": [_node_to_dict(node) for node in self],
        }

    def to_json(self, path: str = None, indent: int = 2) -> str:
        """Serialize the analysis tree to a JSON string.

        Lambda functions are converted to their body expression string so the
        resulting JSON is human-readable and can be loaded back with
        :meth:`from_json`.

        Args:
            path (str, optional): If provided, the JSON is also written to this
                file.  The directory must already exist.  Defaults to ``None``.
            indent (int, optional): Number of spaces used for JSON indentation.
                Defaults to ``2``.

        Returns:
            str: The JSON string representation of the tree.

        See Also:
            from_json : Reconstruct a tree from a JSON string or file.
            to_dict : Serialize to a plain Python dictionary.

        Examples:
            >>> tree = AnalysisTree().split_by("df.Gender").analyze_by(n=lambda df: len(df))
            >>> json_str = tree.to_json()
            >>> reconstructed = AnalysisTree.from_json(json_str)
        """
        result = json.dumps(self.to_dict(), indent=indent)
        if path is not None:
            with open(path, "w", encoding="utf-8") as f:
                f.write(result)
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisTree":
        """Reconstruct an analysis tree from a dictionary.

        The dictionary must have the format produced by :meth:`to_dict`.
        After reconstruction all analysis expressions are stored as strings,
        so running the tree requires the referenced names (e.g. ``np``,
        ``pd``) to be available in the ``environ`` passed to :meth:`run`
        or configured via :meth:`set_default_environ`.

        Args:
            data (dict): A dictionary produced by :meth:`to_dict`.

        Returns:
            AnalysisTree: The reconstructed analysis tree.

        See Also:
            to_dict : Serialize to a dictionary.
            from_json : Reconstruct from a JSON string or file.

        Examples:
            >>> tree = AnalysisTree().split_by("df.Gender").analyze_by(n="len(df)")
            >>> reconstructed = AnalysisTree.from_dict(tree.to_dict())
        """
        nodes = [_dict_to_node(n) for n in data.get("nodes", [])]
        return cls(*nodes, denom=data.get("denom"))

    @classmethod
    def from_json(cls, source: str) -> "AnalysisTree":
        """Reconstruct an analysis tree from a JSON string or file path.

        Automatically detects whether *source* is an existing file path
        (checked via :func:`os.path.isfile`) or a raw JSON string.

        Args:
            source (str): A JSON string or the path to a ``.json`` file
                produced by :meth:`to_json`.

        Returns:
            AnalysisTree: The reconstructed analysis tree.

        Raises:
            json.JSONDecodeError: If *source* is not a valid JSON string.

        See Also:
            to_json : Serialize a tree to JSON.
            from_dict : Reconstruct from a plain dictionary.

        Examples:
            >>> tree = AnalysisTree().split_by("df.Gender").analyze_by(n="len(df)")
            >>> tree.to_json("/tmp/my_tree.json")
            >>> loaded = AnalysisTree.from_json("/tmp/my_tree.json")

            >>> # from a raw JSON string
            >>> json_str = tree.to_json()
            >>> loaded = AnalysisTree.from_json(json_str)
        """
        if os.path.isfile(source):
            with open(source, "r", encoding="utf-8") as f:
                source = f.read()
        return cls.from_dict(json.loads(source))

    def split_by(self, expr: str = None, label: str = None, drop_empty: bool = False, **kwargs):
        """Add a split node at the extremites of the branches.
        Note: 
            No split node is added where there is already a split node or an analysis node with termination signal.
        Args:
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            drop_empty (bool, optional): If True, split levels that produce an empty DataFrame are discarded.
                Defaults to False.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added.
        Examples:
            >>> a_tree = AnalysisTree()
            >>> a_tree = a_tree.split_by(m = "df.A > 50")
            >>> a_tree = a_tree.split_by("df.B > 50")
            >>> a_tree = a_tree.split_by("df.Gender", drop_empty=True)
        """
        
        is_split_node = [isinstance(x, SplitNode) for x in self]
        no_termination = not any([x.termination for x in self if isinstance(x, AnalysisNode)])

        # length 0 OR (no split node and no termination signal)
        if ((len(is_split_node) == 0) or ((not any(is_split_node)) and no_termination)):
            self.append(SplitNode(expr = expr, label = label, drop_empty = drop_empty, **kwargs))
        
        else:
            for i in range(len(self)):
                    if isinstance(self[i], SplitNode):
                        self[i] = self[i].split_by(expr = expr, label = label, drop_empty = drop_empty, **kwargs)
                
        return self
    
    def split_at_by(self, path: list, expr: str = None, label:str = None, drop_empty: bool = False, **kwargs):
        """Add a split node at a specific path in the tree.
        
        Args:
            path (list): A list representing the path where the split node should be added.
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
            drop_empty (bool, optional): If True, split levels that produce an empty DataFrame are discarded.
                Defaults to False.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added at the specified path.
        Examples:
            >>> a_tree = AnalysisTree()
            >>> a_tree = a_tree.split_by(m = "df.A > 50", label = "A")
            >>> a_tree = a_tree.split_at_by([], "df.B > 50", label = "B") # Add split at root
            >>> a_tree = a_tree.split_at_by(["A"], "df.C > 10", label = "C") # Add split downstream of A only
            >>> a_tree = a_tree.split_at_by(["*", "C"], "df.D > 5", label = "D") # Add split downstream of anything followed by C
            >>> print(a_tree)

        """
        
        if (len(path) == 0):
            self.append(SplitNode(expr = expr, label = label, drop_empty = drop_empty, **kwargs))

        else:
            for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    if (self[i].label == path[0]) or (path[0] == "*"):
                        self[i] = self[i].split_at_by(path = path[1:], expr = expr, label = label, drop_empty = drop_empty, **kwargs)
        
        return self
    
    def split_at_root_by(self, expr: str = None, label:str = None, drop_empty: bool = False, **kwargs):
        """Add a split node at the root of the tree.
        
        Unlike split_by() which adds splits at leaf nodes, this method always adds
        a split at the root level regardless of the current tree structure.
        
        Args:
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added at the root.
        
        Examples:
            >>> tree = AnalysisTree()
            >>> tree = tree.split_by('df.Gender')  # Split at leaves
            >>> tree = tree.split_at_root_by('df.Country')  # Force split at root
            
            >>> # Using keyword arguments
            >>> tree = tree.split_at_root_by(US='df.Country == "US"', UK='df.Country == "UK"')
        
        See Also:
            split_by : Add splits at leaf nodes.
            split_at_by : Add splits at a specific path.
        """
        self.append(SplitNode(expr = expr, label = label, drop_empty = drop_empty, **kwargs))

        return self
    
    def analyze_by(self, *args, label: str = str(), termination: bool = True, **kwargs):
        """Add an analysis node at the extremites of the branches.
        
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to True.
            **kwargs: Keyword arguments where keys are analysis names and values are their
                corresponding expressions. Each value can be a string expression or a callable.
                Callables are dispatched by parameter name:

                - ``lambda df: ...`` — receives the current-level DataFrame.
                - ``lambda _N: ...`` — receives the denominator count list
                  (requires ``denom`` to be set on the :class:`AnalysisTree`).
                - ``lambda df, _N: ...`` — receives both the DataFrame and the count list.

                When ``denom`` is set, ``_N`` is a list of cumulative unique counts from root
                to the current level: ``_N[0]`` is the full-dataset count and ``_N[-1]`` is
                the current-level count.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new analysis node added.
        Examples:
            >>> a_tree = AnalysisTree()
            >>> a_tree = a_tree.analyze_by(mean=lambda df: np.mean(df.A), std=lambda df: np.std(df.B))
            >>> # Using _N for proportions (requires denom to be set on the tree):
            >>> a_tree = (AnalysisTree(denom="ID")
            ...     .split_by("df.Gender")
            ...     .analyze_by(
            ...         mean_income=lambda df: np.mean(df.Income),
            ...         prop=lambda _N: _N[-1] / _N[0],
            ...     ))
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
        """Add an analysis node without a termination signal at the extremities of the branches.
        
        This is a convenience method equivalent to analyze_by() with termination=False.
        Nodes added with this method allow further splits to be added after them,
        enabling intermediate summary statistics in the tree.
        
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to False.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.
        
        Returns:
            AnalysisTree: The modified AnalysisTree with the new summary node added.
        
        Examples:
            >>> tree = AnalysisTree()
            >>> tree = tree.summarize_by(intermediate_count=lambda df: len(df))
            >>> tree = tree.split_by('df.Gender')  # Can still add splits after summarize
            >>> tree = tree.analyze_by(final_mean=lambda df: np.mean(df.Income))  # Terminal analysis
        
        See Also:
            analyze_by : Add terminal analysis nodes (termination=True).
            summarize_at_by : Add summary at a specific path.
        """
        self.analyze_by(*args, label = label, termination = termination, **kwargs)
        return self
    
    def summarize_at_by(self, path: list, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at a specific path in the tree.
        
        This is a convenience method equivalent to analyze_at_by() with termination=False.
        Allows adding intermediate summary statistics at a specific location in the tree.
        
        Args:
            path (list): A list representing the path where the summary node should be added.
                Use ["*"] to apply to all branches at a given level. Note that the elements of that path correspond to the labels of the split node,
                NOT the levels of the data that are being analyzed.
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to False.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.
        
        Returns:
            AnalysisTree: The modified AnalysisTree with the new summary node added.
        
        Examples:
            >>> tree = AnalysisTree()
            >>> tree = tree.split_by('df.Gender', label="Gender").split_by('df.Country', label="Country")
            >>> tree = tree.summarize_at_by(["Gender"], n=lambda df: len(df), label="Count")
        
        See Also:
            analyze_at_by : Add terminal analysis at a specific path.
            summarize_by : Add summary at all leaf nodes.
        """
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
            >>> a_tree = AnalysisTree()
            >>> a_tree.split_by(m = "df.A > 50")
            >>> a_tree = a_tree.cross_analyze_by(m = "np.mean(df.A) - np.mean(ref_df.A)", s = "np.median(df.B) - np.median(ref_df.B)")
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
    def __init__(self, *args, expr:str = None, label:str = None, drop_empty: bool = False, **kwargs) -> None:
        """
        Initializes the SplitNode object.
        Args:
            *args: Additional positional arguments.
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
            drop_empty (bool, optional): If True, split levels that produce an empty DataFrame are discarded
                from the result. Defaults to False (all levels are kept, even empty ones).
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Raises:
            AssertionError: If neither `expr` nor `kwargs` are provided, or if both are provided.
        Returns:
            None
        Examples:
            >>> SplitNode("age > 50")
            >>> SplitNode(Y = "age > 50", N = "age <= 50")
            >>> SplitNode("df.Age > 50", drop_empty=True)  # discard empty groups
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
        self.drop_empty = drop_empty

    def __str__(self, ind: int = 0, is_last: bool = True, prefix: str = ""):
        """Return a string representation of the split node.
        
        Args:
            ind (int): Indentation level for nested display. Defaults to 0 (deprecated, use prefix).
            is_last (bool): Whether this is the last child of its parent. Defaults to True.
            prefix (str): The prefix string from parent levels. Defaults to "".
            
        Returns:
            str: Formatted representation of the split and its children.
        """
        # Build the node expression string
        if self.expr is not None:
            res = self.str
        else:
            expr_lst = [f"{k}: {v}" for k,v in self.str.items()]
            res = " -- ".join(expr_lst)

        # Choose connector based on position
        connector = "└─ " if is_last else "├─ "
        split_str = prefix + connector + f"Split Node {self.label}: [" + res + "]\n"
        
        # Build prefix for children
        child_prefix = prefix + ("   " if is_last else "│  ")
        
        # Process children
        result = [split_str]
        for i, child in enumerate(self):
            child_is_last = (i == len(self) - 1)
            result.append(child.__str__(is_last=child_is_last, prefix=child_prefix))
        
        return "".join(result)

    def run(self, data: pd.DataFrame, environ: dict = None, denom=None, _N=None) -> SplitDataNode:
        """Run the split node on the provided DataFrame.
        Args:
            data (pd.DataFrame): The DataFrame to split.
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
            denom (str or list of str, optional): The column name(s) used as the denominator for unique counts. Defaults to None.
        Returns:
            SplitDataNode: The resulting SplitDataNode after running the split node.
        Examples:
            >>> a_node = AnalysisNode(m = "1", s = "2")  # no eval in analysis
            >>> s_node = SplitNode(a_node, a_node, expr = "df.B > 50")
            >>> a_tree = AnalysisTree(s_node, a_node)
            >>> df = pd.DataFrame({
            ...     "A": [10, 11, 12, 14, 15, 16],
            ...     "B": [10, 20, 40 ,50 ,60, 100]
            ... })
            >>> res = a_tree.run(df)
        """

        if self.expr is not None:
            # Split using a single expression.
            gp_eval_dict = scope_eval(df = data, extra_context = environ, **{"gp": self.expr})
            gp_bool = gp_eval_dict["gp"]

            groups = data.groupby(gp_bool, observed=True)
                
            # Convert to dictionary of DataFrames
            split_dfs = {str(name): group for name, group in groups}

        else:
            # Split using multiple expressions.
            # Note: Group might overlap or not cover all rows.
            split_dfs = {}
            gp_eval_dict = scope_eval(df = data, extra_context = environ, **self.kwexpr)
            for n, gp in gp_eval_dict.items():
                split_dfs.update({n: data[gp]})
        if self.drop_empty:
            split_dfs = {k: v for k, v in split_dfs.items() if len(v) > 0}
        # Recursively apply run for each data frame (that now contain the name of the groups), 
        # create a lvlnode which contains the rest of the tree
        # the self of the lvl node is the rest of the tree on which run has been applied
        # res_dic = {str(n): LvlDataNode(split_lvl = str(n), _N = count_or_length(data, id), **{str(nn): element.run(data, environ = environ, id = id, _N = None) for nn, element in enumerate(self)}) for n, data in split_dfs.items()}

        # Selectt the elements of self that are not CrossAnalysisNode

        not_cross_analysis_node = {nn: element for nn, element in enumerate(self) if not isinstance(element, CrossAnalysisNode)}
        cross_analysis_node = {nn: element for nn, element in enumerate(self) if isinstance(element, CrossAnalysisNode)}

        res_dic = {}
        for n, subset in split_dfs.items():
            _N_new = _N + [count_or_length(subset, denom)] if denom is not None else None
            child_results = {(str(element.label) or str(nn)): element.run(subset, environ=environ, denom=denom, _N=_N_new) for nn, element in not_cross_analysis_node.items()}
            res_dic[str(n)] = LvlDataNode(split_lvl=str(n), _N=_N_new, **child_results)

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
                        _N_cross = _N + [count_or_length(var_df, denom)] if denom is not None else None
                        res_dic[cross_label] = LvlDataNode(split_lvl = cross_label, _N = _N_cross, **{(str(element.label) or str(nn)): element.run(cross_data, environ = environ, denom = denom, _N = _N_cross) for nn, element in cross_analysis_node.items()})
                
                # If no reference level is specified, compare every level with each other.
                else:
                    df_keys = list(split_dfs.keys())
                    for ref_lvl_i in range(len(df_keys) - 1):
                        ref_df = split_dfs[df_keys[ref_lvl_i]]
                        for var_lvl_i in range(ref_lvl_i + 1, len(df_keys)):
                            var_df = split_dfs[df_keys[var_lvl_i]]
                            cross_data = { "df": var_df, "ref_df": ref_df }
                            cross_label = f"{df_keys[var_lvl_i]}_vs_{df_keys[ref_lvl_i]}"
                            _N_cross = _N + [count_or_length(var_df, denom)] if denom is not None else None
                            res_dic[cross_label] = LvlDataNode(split_lvl = cross_label, _N = _N_cross, **{(str(element.label) or str(nn)): element.run(cross_data, environ = environ, denom = denom, _N = _N_cross) for nn, element in cross_analysis_node.items()})


        split_var = self.expr or "::".join(self.kwexpr.keys())

        return SplitDataNode(split_var = split_var, label = self.label, **res_dic)
    
    def split_by(self, expr: str = None, label:str = None, drop_empty: bool = False, **kwargs):
        """Add a split node at the extremites of the branches.

        Note: 
            No split node is added where there is already a split node or an analysis node with termination signal.
        Args:
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
            drop_empty (bool, optional): If True, split levels that produce an empty DataFrame are discarded.
                Defaults to False.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added.
        Examples:
            >>> a_tree = AnalysisTree()
            >>> a_tree = a_tree.split_by(m = "A > 50")
            >>> a_tree = a_tree.split_by("B > 50")
        """
            
        is_split_node = [isinstance(x, SplitNode) for x in self]
        no_termination = not any([x.termination for x in self if isinstance(x, AnalysisNode)])
        
        # length 0 OR (no split node and no termination signal)
        if ((len(is_split_node) == 0) or ((not any(is_split_node)) and no_termination)):
            self.append(SplitNode(expr = expr, label = label, drop_empty = drop_empty, **kwargs))
        
        else:
            for i in range(len(self)):
                    if isinstance(self[i], SplitNode):
                        self[i] = self[i].split_by(expr = expr, label = label, drop_empty = drop_empty, **kwargs)
                
        return self
    
    def split_at_by(self, path: list, expr: str = None, label:str = None, drop_empty: bool = False, **kwargs):
        """Add a split node at a specific path in the tree.
        
        Args:
            path (list): A list representing the path where the split node should be added. Use ["*"] to apply to all branches at a given level. Note that the elements of that path correspond to the labels of the split node,
                NOT the levels of the data that are being analyzed.
            expr (str, optional): The representation of an expression or the name of a column to be used for splitting the data.
            label (str, optional): The label of the node.
            drop_empty (bool, optional): If True, split levels that produce an empty DataFrame are discarded.
                Defaults to False.
            **kwargs: Keyword arguments mapping group names to their corresponding split expressions.
        Returns:
            AnalysisTree: The modified AnalysisTree with the new split node added at the specified path.
        Examples:
            >>> tree = AnalysisTree()
            >>> tree.split_by('df.Gender', label="Gender")
            >>> tree.split_by('df.Country', label="US vs non-US")
            >>> tree.split_at_by(["Gender"], "df.Income") # Add split by income downstream of the gender split.
            >>> tree.split_at_by(["*", "US vs non-US"], "df.Age") # Add split by age downstream of the US vs non-US split.
            >>> tree.split_at_by([], "df.Education") # Add split by education at the root of the tree (i.e. before any other splits)
        """
        
        if (len(path) == 0):
            self.append(SplitNode(expr = expr, label = label, drop_empty = drop_empty, **kwargs))

        else:
            for i in range(len(self)):
                if isinstance(self[i], SplitNode):
                    if (self[i].label == path[0]) or (path[0] == "*"):
                        self[i] = self[i].split_at_by(path = path[1:], expr = expr, label = label, drop_empty = drop_empty, **kwargs)
        
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
            >>> a_tree = AnalysisTree()
            >>> a_tree = a_tree.analyze_by(m = "np.mean(A)", s = "np.std(B)")
            >>> a_tree = a_tree.analyze_by("np.mean(A)", "np.std(B)", label = "Summary Stats")
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
        """Add an analysis node without a termination signal at the extremites of the branches.
        
        This is a convenience method equivalent to analyze_by() with termination=False.
        Nodes added with this method allow further splits to be added after them,
        enabling intermediate summary statistics in the tree.
        
        Args:
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to False.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.
        
        Returns:
            SplitNode: The modified SplitNode with the new summary node added.
        
        Examples:
            >>> node = SplitNode(expr='df.Gender')
            >>> node = node.summarize_by(intermediate_count=lambda df: len(df))
            >>> node = node.split_by('df.Country')  # Can still add splits
        
        See Also:
            analyze_by : Add terminal analysis nodes.
            summarize_at_by : Add summary at a specific path.
        """

        self.analyze_by(*args, label = label, termination = termination, **kwargs)
        return self

    def summarize_at_by(self, path: list, *args, label: str = str(), termination: bool = False, **kwargs):
        """Add an analysis node without a termination signal at a specific path in the tree.
        
        This is a convenience method equivalent to analyze_at_by() with termination=False.
        Allows adding intermediate summary statistics at a specific location in the tree.
        
        Args:
            path (list): A list representing the path where the summary node should be added.
                Use ["*"] to apply to all branches at a given level.
            *args: Additional positional arguments representing analysis expressions.
            label (str, optional): The label for the analysis node. Defaults to an empty string.
            termination (bool, optional): Indicates if this node is a termination node. Defaults to False.
            **kwargs: Keyword arguments where keys are analysis names and values are their corresponding expressions.
        
        Returns:
            SplitNode: The modified SplitNode with the new summary node added.
        
        Examples:
            >>> tree = AnalysisTree()
            >>> tree.split_by('df.Gender', label="Gender")
            >>> tree.split_by('df.Country', label="US vs non-US")
            >>> tree.summarize_at_by(["Gender"], n=lambda df: len(df), label="Count") # Add summary by count downstream
            >>> tree.summarize_at_by(["*", "US vs non-US"], m=lambda df: np.mean(df.Income), label="Mean Income") # Add summary by mean income downstream of the US vs non-US split.
            >>> print(tree)

        See Also:
            analyze_at_by : Add terminal analysis at a specific path.
            summarize_by : Add summary at all leaf nodes.
        """
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
            >>> a_tree = AnalysisTree()
            >>> a_tree.split_by(m = "df.A > 50")
            >>> a_tree = a_tree.cross_analyze_by(m = "np.mean(df.A) - np.mean(ref_df.A)", s = "np.median(df.B) - np.median(ref_df.B)")
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
            >>> AnalysisNode(m = "np.mean(df.A)", s = "np.std(df.B)")
            >>> AnalysisNode("np.mean(df.A)", "np.std(df.B)", label = "Summary Stats") 
            >>> AnalysisNode("np.mean(df.A)", "np.std(df.B)", label = "Summary Stats", termination = False)
        """

        analysis = {k: k for k in args} | kwargs
        assert len(analysis) > 0, "At least one analysis must be provided"

        self.analysis = analysis
         
        # take the first element of analysis
        self.analysis_str = {k: analysis_to_string(v) for k,v in analysis.items()}
        self.label = label
        self.termination = termination

    def __str__(self, ind: int = 0, is_last: bool = True, prefix: str = ""):
        """Return a string representation of the analysis node.
        
        Args:
            ind (int): Indentation level for nested display. Defaults to 0 (deprecated, use prefix).
            is_last (bool): Whether this is the last child of its parent. Defaults to True.
            prefix (str): The prefix string from parent levels. Defaults to "".
            
        Returns:
            str: Formatted representation of the analysis and its computations.
        """
        # Choose connector based on position
        connector = "└─ " if is_last else "├─ "
        node_header = prefix + connector + f"Analysis Node: {self.label}\n"
        
        # Build prefix for analysis details
        detail_prefix = prefix + ("   " if is_last else "│  ")
        
        # Format analysis details with box-drawing characters
        analysis_items = list(self.analysis_str.items())
        analysis_lines = []
        for i, (key, value) in enumerate(analysis_items):
            detail_is_last = (i == len(analysis_items) - 1)
            detail_connector = "└─ " if detail_is_last else "├─ "
            analysis_lines.append(detail_prefix + detail_connector + f"{key}: {value}\n")
        
        return node_header + "".join(analysis_lines)
    
    def run(self, data, environ = None, denom=None, _N=None) -> DataNode:
        """Run the analysis node on the provided DataFrame.
        Args:
            data (pd.DataFrame): The DataFrame to analyze.
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
            _N (list or None): Cumulative denominator count list passed from the parent split. Defaults to None.
        Returns:
            DataNode: The resulting DataNode after running the analysis node.
        Examples:
            >>> import numpy as np
            >>> a_node = AnalysisNode(m = "np.mean(df.A)", s = "np.std(df.B)")
            >>> df = pd.DataFrame({
            ...     "A": [10, 20],
            ...     "B": [10, 10]
            ... })
            >>> res = a_node.run(df)
            >>> assert res.summary == {"m": np.float64(15), "s": np.float64(0)}
        """

        res = scope_eval(df = data, extra_context = environ, _N = _N, **self.analysis)
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
            >>> CrossAnalysisNode("np.mean(df1.A) - np.mean(df2.A)", "np.median(df1.B) - np.median(df2.B)", label = "Summary Stats") 
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

    def __str__(self, ind: int = 0, is_last: bool = True, prefix: str = ""):
        """Return a string representation of the cross-analysis node.
        
        Args:
            ind (int): Indentation level for nested display. Defaults to 0 (deprecated, use prefix).
            is_last (bool): Whether this is the last child of its parent. Defaults to True.
            prefix (str): The prefix string from parent levels. Defaults to "".
            
        Returns:
            str: Formatted representation of the cross-analysis and its computations.
        """
        # Choose connector based on position
        connector = "└─ " if is_last else "├─ "
        node_header = prefix + connector + f"Cross Analysis Node: {self.label}\n"
        
        # Build prefix for analysis details
        detail_prefix = prefix + ("   " if is_last else "│  ")
        
        # Format analysis details with box-drawing characters
        analysis_items = list(self.analysis_str.items())
        analysis_lines = []
        for i, (key, value) in enumerate(analysis_items):
            detail_is_last = (i == len(analysis_items) - 1)
            detail_connector = "└─ " if detail_is_last else "├─ "
            analysis_lines.append(detail_prefix + detail_connector + f"{key}: {value}\n")
        
        return node_header + "".join(analysis_lines)
    
    def run(self, data: dict, environ = None, denom=None, _N=None) -> DataNode:
        """Run the cross-analysis node on the provided DataFrames.
        Args:
            data (dict): A dictionary containing two DataFrames to analyze. Keys should be "df" and "ref_df".
            environ (dict, optional): A dictionary representing the environment in which to evaluate expressions. Defaults to None.
            _N (list or None): Cumulative denominator count list passed from the parent split. Defaults to None.
        Returns:
            DataNode: The resulting DataNode after running the cross-analysis node.
        """

        res = scope_cross_eval(df = data["df"], ref_df = data["ref_df"], extra_context = environ, _N = _N, **self.analysis)
        return DataNode(data = data["df"], summary = res, label = self.label, depth = 0, _N = _N) # TODO: do we need another class for cross data node?

#endregion

#region JSON

def _node_to_dict(node) -> dict:
    """Serialize a single tree node to a JSON-serializable dict.

    Dispatches on the type of *node* (``SplitNode``, ``AnalysisNode``, or
    ``CrossAnalysisNode``).  Callable values (lambdas) in analysis or split
    expressions are converted to their body string via
    :func:`~pyMyriad.utils._callable_to_expr_str`.

    Args:
        node: A ``SplitNode``, ``AnalysisNode``, or ``CrossAnalysisNode``.

    Returns:
        dict: A JSON-serializable representation of *node*.

    Raises:
        TypeError: If *node* is not a recognized tree node type.
    """
    if isinstance(node, CrossAnalysisNode):
        analysis_ser = {
            k: (_callable_to_expr_str(v) if callable(v) else v)
            for k, v in node.analysis.items()
        }
        return {
            "type": "CrossAnalysisNode",
            "label": node.label,
            "termination": node.termination,
            "ref_lvl": node.ref_lvl,
            "analysis": analysis_ser,
        }
    elif isinstance(node, AnalysisNode):
        analysis_ser = {
            k: (_callable_to_expr_str(v) if callable(v) else v)
            for k, v in node.analysis.items()
        }
        return {
            "type": "AnalysisNode",
            "label": node.label,
            "termination": node.termination,
            "analysis": analysis_ser,
        }
    elif isinstance(node, SplitNode):
        if node.expr is not None:
            expr_ser = _callable_to_expr_str(node.expr) if callable(node.expr) else node.expr
            split_data = {"expr": expr_ser}
        else:
            kwexpr_ser = {
                k: (_callable_to_expr_str(v) if callable(v) else v)
                for k, v in node.kwexpr.items()
            }
            split_data = {"kwexpr": kwexpr_ser}
        return {
            "type": "SplitNode",
            "label": node.label,
            "drop_empty": node.drop_empty,
            **split_data,
            "nodes": [_node_to_dict(child) for child in node],
        }
    else:
        raise TypeError(f"Cannot serialize node of type {type(node).__name__!r}")


def _dict_to_node(data: dict):
    """Reconstruct a tree node from a serialized dict.

    The dict must have a ``"type"`` key matching one of ``"SplitNode"``,
    ``"AnalysisNode"``, or ``"CrossAnalysisNode"``.  After reconstruction all
    analysis expressions are plain strings; running the tree requires that the
    referenced names (e.g. ``np``) are available in ``environ``.

    Args:
        data (dict): A dictionary produced by :func:`_node_to_dict`.

    Returns:
        SplitNode | AnalysisNode | CrossAnalysisNode: The reconstructed node.

    Raises:
        ValueError: If ``data["type"]`` is not a recognized node type.
    """
    node_type = data.get("type")
    if node_type == "AnalysisNode":
        return AnalysisNode(
            label=data["label"],
            termination=data["termination"],
            **data["analysis"],
        )
    elif node_type == "CrossAnalysisNode":
        return CrossAnalysisNode(
            label=data["label"],
            termination=data["termination"],
            ref_lvl=data["ref_lvl"],
            **data["analysis"],
        )
    elif node_type == "SplitNode":
        children = [_dict_to_node(c) for c in data.get("nodes", [])]
        if "expr" in data:
            return SplitNode(
                *children,
                expr=data["expr"],
                label=data["label"],
                drop_empty=data["drop_empty"],
            )
        else:
            return SplitNode(
                *children,
                label=data["label"],
                drop_empty=data["drop_empty"],
                **data["kwexpr"],
            )
    else:
        raise ValueError(f"Unknown node type: {node_type!r}")

#endregion


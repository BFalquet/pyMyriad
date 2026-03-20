"""Data tree result structures module.

This module provides classes for storing the results of running an AnalysisTree
on data. The tree structure mirrors the AnalysisTree but contains actual computed
values instead of analysis specifications.

The main classes are:
- DataTree: The root container for analysis results
- SplitDataNode: Results organized by split groups
- LvlDataNode: Results for a specific level within a split
- DataNode: Leaf node containing actual computed values

DataTree objects are typically created by running an AnalysisTree on data:
    >>> result = analysis_tree.run(df)
    >>> isinstance(result, DataTree)  # True

DataTree objects can be flattened to pandas DataFrames for export and visualization.
"""

import pandas as pd
import numpy as np
from .utils import scope_eval, get_top_globals, analysis_to_string, count_or_length

class DataNode():
    """Represents a node in a data tree structure, holding data and metadata.
    
    Attributes:
        data: The data associated with this node. Can be any type.
        summary (dict): A dictionary containing summary information about the node.
        label (str): A string label identifying the node.
        depth (int): The depth of the node in the tree structure.
        _N (int): The number of unique identifiers in the data, if applicable.
    """

    def __init__(self, data = None, summary: dict = None, label: str = str(), depth: int = 0, _N: int = None):
        """Initializes the DataNode object.
        Args:
            data: The data associated with this node. Can be any type. Defaults to None.
            summary (dict, optional): A dictionary containing summary information about the node. Defaults to None.
            label (str, optional): A string label identifying the node. Defaults to an empty string.
            depth (int, optional): The depth of the node in the tree structure. Defaults to 0.
        Examples:
            >>> DataNode(data = df, summary = {"mean": 5}, label = "Summary", depth = 1)
        """
        
        self.data = data
        self.summary = summary
        self.label = label
        self.depth = depth
        self._N = _N

    def __str__(self, ind: int = 0):
        """Return a string representation of the data node.
        
        Args:
            ind (int): Indentation level for nested display. Defaults to 0.
            
        Returns:
            str: Formatted representation of the node's summary statistics.
        """
        res = [f"{' ' * (ind * 2)}  └- {k}: {str(v)}\n" for k,v in (self.summary or {}).items()]
        return f"{' ' * (ind * 2)}  analysis: {self.label}\n" + "".join(res)
    
    def __flatten__(self, path = (), depth: int = 0, pivot_var = (), pivot_now: bool = False, path_pivot = (), pivot_split = (), pivot_lvl = (), data:bool = False) -> pd.DataFrame:

        path = path + ("analysis",)
        path_pivot = path_pivot + ("analysis",)
        
        return pd.DataFrame({
            'type': ['analysis'],
            'split': [None],
            'lvl': [None],
            'path': [list(path)],
            'path_pivot': [list(path_pivot)],
            'pivot_split': [list(pivot_split)],
            'pivot_lvl': [list(pivot_lvl)],
            'depth': depth,
            'label': self.label,
            'summary': [self.data] if data else [self.summary]
        }, index = [0])


class SplitDataNode(dict):
    """A node representing a split in a hierarchical data structure.
    
    This class inherits from `dictionnary` and is intended to contain child nodes of type `LvlDataNode`.
    Each `SplitDataNode` is associated with a splitting variable, specified by `split_var`.

    Attributes:
        split_var (str): The variable name used for splitting.
    """

    def __init__(self, split_var: str, label: str = None, **kwargs):
        """Initializes the SplitDataNode object.
        
        Args:
            split_var (str): The variable name used for splitting.
            label (str, optional): The label for the split node. Defaults to None.
            **kwargs: Keyword arguments where each value must be an instance of LvlDataNode.
        Attributes:
            split_var (str): The variable name used for splitting.
        Raises:
            AssertionError: If any value in kwargs is not an instance of LvlDataNode.
        Returns:
            None
        Examples:
            >>> SplitDataNode()
        """

        acceptable_lst = [isinstance(x, (LvlDataNode)) for x in kwargs.values()] 
        assert all(acceptable_lst), "All elements must be instances of LvlDataNode"
        super().__init__(**kwargs)
        self.split_var = split_var
        self.label = label or analysis_to_string(split_var)

    def __str__(self, ind: int = 0):
        """Return a string representation of the split data node.
        
        Args:
            ind (int): Indentation level for nested display. Defaults to 0.
            
        Returns:
            str: Formatted representation of the split and its levels.
        """
        res = [x.__str__(ind = ind + 1) for x in self.values()]
        recusive_str = "".join(res)
        return f"{' ' * (ind * 2)}Split: {self.label}\n" + recusive_str
    
    def __flatten__(self, path = (), depth: int = 0, pivot_var = (), path_pivot = (), pivot_split = (), pivot_lvl = (), data:bool = False) -> pd.DataFrame:

        path = path + (self.label,) # split_var

        if self.label in pivot_var:
            path_pivot = path_pivot
            pivot_split = pivot_split + (self.label,)
            pivot_now = True

        else:
            path_pivot = path_pivot + (self.label,)
            pivot_now = False

        res_loc = pd.DataFrame({
            'type': ['split'],
            'split': [self.label],
            'lvl': [None],
            'path': [list(path)],
            'path_pivot': [list(path_pivot)],
            'pivot_split': [list(pivot_split)],
            'pivot_lvl': [list(pivot_lvl)],
            'depth': depth,
            'summary': [None],
            'label': None,
        })

        res = [x.__flatten__(path = path, depth = depth + 1, pivot_var = pivot_var, pivot_now = pivot_now, path_pivot = path_pivot, pivot_split = pivot_split, pivot_lvl = pivot_lvl, data = data) for x in self.values()]

        res = [res_loc] + res
        return pd.concat(res, ignore_index = True)
    

class LvlDataNode(dict):
    """A subclass of dictionnary that represents a hierarchical data node at a specific split level.

    Attributes:
        split_lvl (str): The identifier for the split level of this node.
        meta (any): Metadata associated with this node.
        _N (int): The number of unique identifiers in the data, if applicable.
    """

    def __init__(self, split_lvl: str, meta: any = (), _N: int = None, **kwargs):
        """Initializes the LvlDataNode object.
        Args:
            split_lvl (str): The identifier for the split level of this node.
            meta (any, optional): Metadata associated with this node. Defaults to an empty tuple.
            _N (int, optional): The number of unique identifiers in the data, if applicable. Defaults to None.
            **kwargs: Keyword arguments where each value must be an instance of SplitDataNode or DataNode.
        Raises:
            AssertionError: If any value in kwargs is not an instance of SplitDataNode or DataNode.
        Returns:
            None
        Examples:
            >>> LvlDataNode([], split_lvl = "level1")
        """

        acceptable_lst = [isinstance(x, (SplitDataNode, DataNode)) for x in kwargs.values()] 
        assert all(acceptable_lst)

        assert isinstance (split_lvl, str)
        super().__init__(**kwargs)
        self.split_lvl = split_lvl
        self.meta = meta
        self._N = _N

    def __str__(self, ind: int = 0):
        """Return a string representation of the level data node.
        
        Args:
            ind (int): Indentation level for nested display. Defaults to 0.
            
        Returns:
            str: Formatted representation of the level and its children.
        """
        res = [x.__str__(ind = ind + 1) for x in self.values()]
        recusive_str = "".join(res)
        
        return f"{' ' * (ind * 2)}└- {self.split_lvl}\n" + recusive_str
    
    def __flatten__(self, path = (), depth:int = 0, pivot_var = (), pivot_now: bool = False, path_pivot = (), pivot_split = (), pivot_lvl = (), data:bool = False) -> pd.DataFrame:
        """Flatten a LvlDataNode
        Args:
            path (str): The current path at which the `LvlDataNode` sits. 
            depth (int): The depth at which the the `LvlDataNode` sits. Corresponds in general to the lenght of the `path`.
            pivot_var (str): The name of the split to pivot by. ===> just transmitted further below. 
            pivot_now (bool): whether the `LvlDataNode` sits just after a `SplitDataNode` corresponding to a `pivot_var` and should be pivoted.
            path_pivot (str): The current path without the nodes that have been pivoted. 
            pivot_split (list(str)): The list of the `SplitDataNode` to pivot by that already have been traversed. ===> just transmitted further below.
            pivot_lvl: (list(str)): The list of the `LvlDataNode` to pivot by that already have been traversed.
        """

        path = path + (self.split_lvl,)

        if pivot_now:
            path_pivot = path_pivot # Do not add anything if pivoted.
            pivot_lvl = pivot_lvl + (self.split_lvl,)

        else:
            path_pivot = path_pivot + (self.split_lvl,)


        res_loc = pd.DataFrame({
            'type': ['level'],
            'split': [None],
            'lvl': [self.split_lvl],
            'path': [list(path)],
            'path_pivot': [list(path_pivot)],
            'pivot_split': [list(pivot_split)],
            'pivot_lvl': [list(pivot_lvl)],
            'depth': depth,
            'label': None,
            'summary': [None]
        })

        res = [x.__flatten__(path = path , depth = depth + 1, pivot_var = pivot_var, path_pivot = path_pivot, pivot_split = pivot_split, pivot_lvl = pivot_lvl, data = data) for x in self.values()]
        res = [res_loc] + res
        return pd.concat(res, ignore_index = True)

class DataTree(dict):
    """A subclass of dictionnary that represents a data tree.
    
    Attributes:
        _N (int): The number of unique identifiers in the data, if applicable.
    """
    def __init__(self, _N: int = None, **kwargs):
        """Initializes the DataTree object.
        Args:
            _N (int, optional): The number of unique identifiers in the data, if applicable. Defaults to None.
            **kwargs: Keyword arguments where each value must be an instance of SplitDataNode or DataNode.
        Raises:
            AssertionError: If any value in kwargs is not an instance of SplitDataNode or Data
        Examples:
            >>> DataTree()
        """
        acceptable_lst = [isinstance(x, (SplitDataNode, DataNode)) for x in kwargs.values()] 
        assert all(acceptable_lst)
        super().__init__(**kwargs)
        self._N = _N

    def __str__(self):
        """Return a string representation of the data tree.
        
        Returns:
            str: Formatted tree structure showing splits, levels, and results.
        """
        ind = 0
        res = [x.__str__(ind = ind + 1) for x in self.values()]
        recusive_str = "".join(res)
        return "Data Tree\n" + recusive_str
    
    def __flatten__(self, pivot:str = (), data:bool = False) -> pd.DataFrame:
        """Flatten a DataTree into a DataFrame.
        This method flattens the hierarchical structure of the DataTree into a pandas DataFrame.
        Args:
            pivot (str, optional): The name of a split to pivot by. Defaults to an empty tuple.
        Returns:
            pd.DataFrame: A flattened representation of the DataTree.
        """

        depth = 0
        path = ("root",)
        pivot_split = ()
        pivot_lvl = ()
        path_pivot = ("root",)

        res_loc = pd.DataFrame({
            'type': ['root'],
            'split': [None],
            'lvl': [None],
            'path': [list(path)],
            'path_pivot': [list(path)],
            'pivot_split': [list(())],
            'pivot_lvl': [list(())],
            'depth': depth,
            'label': None,
            'summary': [None]
        })

        res = [x.__flatten__(path = path, depth = depth + 1, pivot_var = pivot, path_pivot = path_pivot, pivot_split = pivot_split, pivot_lvl = pivot_lvl, data = data) for x in self.values()]
        res = [res_loc] + res
        return pd.concat(res, ignore_index = True)

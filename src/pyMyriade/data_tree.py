import pandas as pd
import numpy as np

class DataNode():
    """Represents a node in a data tree structure, holding data and metadata.
    
    Attributes:
        data: The data associated with this node. Can be any type.
        summary (dict): A dictionary containing summary information about the node.
        label (str): A string label identifying the node.
        depth (int): The depth of the node in the tree structure.
    """

    def __init__(self, data = None, summary: dict = None, label: str = str(), depth: int = 0):
        """Initializes the DataNode object.
        Args:
            data: The data associated with this node. Can be any type. Defaults to None.
            summary (dict, optional): A dictionary containing summary information about the node. Defaults to None.
            label (str, optional): A string label identifying the node. Defaults to an empty string.
            depth (int, optional): The depth of the node in the tree structure. Defaults to 0.
        Examples:
            DataNode(data = df, summary = {"mean": 5}, label = "Summary", depth = 1)
        """
        
        self.data = data
        self.summary = summary
        self.label = label
        self.depth = depth

    def __str__(self, ind: int = 0):

        res = [f"{' ' * (ind * 2)}  {k}: {str(v)}\n" for k,v in (self.summary or {}).items()]
        return f"{' ' * (ind * 2)}analysis {self.label}:\n" + "".join(res)
    
    def __flatten__(self, path = (), depth: int = 0, pivot_var = (), pivot_now: bool = False, path_pivot = (), pivot_split = (), pivot_lvl = ()) -> pd.DataFrame:

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
            'summary': [self.summary]
        }, index = [0])


class SplitDataNode(dict):
    """A node representing a split in a hierarchical data structure.
    
    This class inherits from `dictionnary` and is intended to contain child nodes of type `LvlDataNode`.
    Each `SplitDataNode` is associated with a splitting variable, specified by `split_var`.

    Attributes:
        split_var (str): The variable name used for splitting.
    """

    def __init__(self, split_var: str, **kwargs):
        """Initializes the SplitDataNode object.
        
        Args:
            split_var (str): The variable name used for splitting.
            **kwargs: Keyword arguments where each value must be an instance of LvlDataNode.
        Attributes:
            split_var (str): The variable name used for splitting.
        Raises:
            AssertionError: If any value in kwargs is not an instance of LvlDataNode.
        Returns:
            None
        Examples:
            SplitDataNode()
        """

        acceptable_lst = [isinstance(x, (LvlDataNode)) for x in kwargs.values()] 
        assert all(acceptable_lst), "All elements must be instances of LvlDataNode"
        super().__init__(**kwargs)
        self.split_var = split_var

    def __str__(self, ind: int = 0):
        
        res = [x.__str__(ind = ind + 1) for x in self.values()]
        recusive_str = "".join(res)
        return f"{' ' * (ind * 2)}Split node on {self.split_var}\n" + recusive_str
    
    def __flatten__(self, path = (), depth: int = 0, pivot_var = (), path_pivot = (), pivot_split = (), pivot_lvl = ()) -> pd.DataFrame:

        path = path + (self.split_var,)

        if self.split_var in pivot_var:
            path_pivot = path_pivot
            pivot_split = pivot_split + (self.split_var,)
            pivot_now = True

        else:
            path_pivot = path_pivot + (self.split_var,)
            pivot_now = False

        res_loc = pd.DataFrame({
            'type': ['split'],
            'split': [self.split_var],
            'lvl': [None],
            'path': [list(path)],
            'path_pivot': [list(path_pivot)],
            'pivot_split': [list(pivot_split)],
            'pivot_lvl': [list(pivot_lvl)],
            'depth': depth,
            'label': None,
            'summary': [None]
        })

        res = [x.__flatten__(path = path, depth = depth + 1, pivot_var = pivot_var, pivot_now = pivot_now, path_pivot = path_pivot, pivot_split = pivot_split, pivot_lvl = pivot_lvl) for x in self.values()]

        res = [res_loc] + res
        return pd.concat(res, ignore_index = True)
    

class LvlDataNode(dict):
    """A subclass of dictionnary that represents a hierarchical data node at a specific split level.

    Attributes:
        split_lvl (str): The identifier for the split level of this node.
        meta (any): Metadata associated with this node.
    """

    def __init__(self, split_lvl: str, meta: any = (), **kwargs):
        """Initializes the LvlDataNode object.
        Args:
            split_lvl (str): The identifier for the split level of this node.
            meta (any, optional): Metadata associated with this node. Defaults to an empty tuple.
            **kwargs: Keyword arguments where each value must be an instance of SplitDataNode or DataNode.
        Raises:
            AssertionError: If any value in kwargs is not an instance of SplitDataNode or DataNode.
        Returns:
            None
        Examples:
            LvlDataNode([], split_lvl = "level1")
        """

        acceptable_lst = [isinstance(x, (SplitDataNode, DataNode)) for x in kwargs.values()] 
        assert all(acceptable_lst)

        assert isinstance (split_lvl, str)
        super().__init__(**kwargs)
        self.split_lvl = split_lvl
        self.meta = meta

    def __str__(self, ind: int = 0):
        
        res = [x.__str__(ind = ind + 1) for x in self.values()]
        recusive_str = "".join(res)
        
        return f"{' ' * (ind * 2)}-- {self.split_lvl}\n" + recusive_str
    
    def __flatten__(self, path = (), depth:int = 0, pivot_var = (), pivot_now: bool = False, path_pivot = (), pivot_split = (), pivot_lvl = ()) -> pd.DataFrame:
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

        res = [x.__flatten__(path = path , depth = depth + 1, pivot_var = pivot_var, path_pivot = path_pivot, pivot_split = pivot_split, pivot_lvl = pivot_lvl) for x in self.values()]
        res = [res_loc] + res
        return pd.concat(res, ignore_index = True)

class DataTree(dict):
    """A subclass of dictionnary that represents a data tree.
    
    Attributes:
        None
    """
    def __init__(self, **kwargs):
        """Initializes the DataTree object.
        Args:
            **kwargs: Keyword arguments where each value must be an instance of SplitDataNode or DataNode.
        Raises:
            AssertionError: If any value in kwargs is not an instance of SplitDataNode or Data
        Examples:
            DataTree()
        """
        acceptable_lst = [isinstance(x, (SplitDataNode, DataNode)) for x in kwargs.values()] 
        assert all(acceptable_lst)
        super().__init__(**kwargs)

    def __str__(self):
        ind = 0
        res = [x.__str__(ind = ind + 1) for x in self.values()]
        recusive_str = "".join(res)
        return "Data Tree\n" + recusive_str
    
    def __flatten__(self, pivot:str = ()) -> pd.DataFrame:
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

        res = [x.__flatten__(path = path, depth = depth + 1, pivot_var = pivot, path_pivot = path_pivot, pivot_split = pivot_split, pivot_lvl = pivot_lvl) for x in self.values()]
        res = [res_loc] + res
        return pd.concat(res, ignore_index = True)

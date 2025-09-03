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
    
    def __flatten__(self, path = (), depth: int = 0) -> pd.DataFrame:

        path = path + ("analysis",)
        
        return pd.DataFrame({
            'type': ['analysis'],
            'split': [None],
            'lvl': [None],
            'path': [list(path)],
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
    
    def __flatten__(self, path = (), depth: int = 0) -> pd.DataFrame:

        path = path + (self.split_var,)

        res_loc = pd.DataFrame({
            'type': ['split'],
            'split': [self.split_var],
            'lvl': [None],
            'path': [list(path)],
            'depth': depth,
            'label': None,
            'summary': [None]
        })

        res = [x.__flatten__(path = path, depth = depth + 1) for x in self.values()]

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
    
    def __flatten__(self, path = (), depth:int = 0) -> pd.DataFrame:
        path = path + (self.split_lvl,)

        res_loc = pd.DataFrame({
            'type': ['level'],
            'split': [None],
            'lvl': [self.split_lvl],
            'path': [list(path)],
            'depth': depth,
            'label': None,
            'summary': [None]
        })

        res = [x.__flatten__(path = path , depth = depth + 1) for x in self.values()]
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
    
    def __flatten__(self) -> pd.DataFrame:
        depth = 0
        path = ("root",)

        res_loc = pd.DataFrame({
            'type': ['root'],
            'split': [None],
            'lvl': [None],
            'path': [list(path)],
            'depth': depth,
            'label': None,
            'summary': [None]
        })

        res = [x.__flatten__(path = path, depth = depth + 1) for x in self.values()]
        res = [res_loc] + res
        return pd.concat(res, ignore_index = True)

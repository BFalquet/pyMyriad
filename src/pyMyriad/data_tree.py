"""Data tree result structures module.

This module provides classes for storing the results of running an AnalysisTree
on data. The tree structure mirrors the AnalysisTree but contains actual computed
values instead of analysis specifications.

The main classes are:
- DataTree: The root container for analysis results (subclass of dict)
- SplitDataNode: Results organized by split groups (subclass of dict)
- LvlDataNode: Results for a specific level within a split (subclass of dict)
- DataNode: Leaf node containing actual computed values

DataTree objects are typically created by running an AnalysisTree on data:
    >>> result = analysis_tree.run(df)
    >>> isinstance(result, DataTree)  # True

DataTree objects can be flattened to pandas DataFrames for export and visualization:
    >>> from pyMyriad import simple_table
    >>> table = simple_table(result)

Tree Structure Example:
    DataTree
    └─ 'df.Gender' -> SplitDataNode
       ├─ 'Male' -> LvlDataNode
       │  └─ 'analysis' -> DataNode (summary={'mean': 55000, 'count': 3})
       └─ 'Female' -> LvlDataNode
          └─ 'analysis' -> DataNode (summary={'mean': 75000, 'count': 3})

See also:
    - ARCHITECTURE.md: Detailed architectural overview
    - analysis_tree.py: Tree construction classes
    - listing.py: Table generation from DataTree
"""

import json
import math
import os

import pandas as pd

from .utils import analysis_to_string


def _serialize_summary_value(val):
    """Convert a summary value to a JSON-safe Python type.

    Rules:
    - ``None``, ``bool``, ``str`` are returned unchanged.
    - ``int`` is returned unchanged.
    - ``float`` is returned unchanged, **except** NaN and ±infinity which
      become the strings ``"NaN"``, ``"Infinity"``, and ``"-Infinity"``.
    - Numeric-like objects (e.g. ``numpy.int64``, ``numpy.float64``) are
      coerced to the corresponding native Python ``int`` or ``float``; the
      same NaN/infinity rule is then applied to coerced floats.
    - Everything else is converted via ``str(val)``.

    Args:
        val: The value to serialize.

    Returns:
        A JSON-serializable Python object.
    """
    if val is None or isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        if math.isnan(val):
            return "NaN"
        if math.isinf(val):
            return "Infinity" if val > 0 else "-Infinity"
        return val
    # Attempt numeric coercion (handles numpy scalars, etc.)
    try:
        float_val = float(val)
        if math.isnan(float_val):
            return "NaN"
        if math.isinf(float_val):
            return "Infinity" if float_val > 0 else "-Infinity"
        # Preserve integer semantics for whole numbers
        int_val = int(val)
        if float_val == int_val:
            return int_val
        return float_val
    except (TypeError, ValueError, OverflowError):
        return str(val)


class DataNode:
    """Represents a node in a data tree structure, holding data and metadata.

    Attributes:
        data: The data associated with this node. Can be any type.
        summary (dict): A dictionary containing summary information about the node.
        label (str): A string label identifying the node.
        depth (int): The depth of the node in the tree structure.
        _N (list | None): Cumulative unique-count list from root to current level when
            a denominator is set on the :class:`AnalysisTree`. ``None`` when no denominator
            is configured.
    """

    def __init__(
        self,
        data=None,
        summary: dict = None,
        label: str = str(),
        depth: int = 0,
        _N: list | None = None,
    ):
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

    def __str__(self, ind: int = 0, is_last: bool = True, prefix: str = ""):
        """Return a string representation of the data node.

        Args:
            ind (int): Indentation level for nested display. Defaults to 0 (deprecated, use prefix).
            is_last (bool): Whether this is the last child of its parent. Defaults to True.
            prefix (str): The prefix string from parent levels. Defaults to "".

        Returns:
            str: Formatted representation of the node's summary statistics.
        """
        # Choose connector based on position
        connector = "└─ " if is_last else "├─ "
        node_header = prefix + connector + f"analysis: {self.label}\n"

        # Build prefix for analysis details
        detail_prefix = prefix + ("   " if is_last else "│  ")

        # Format analysis details with box-drawing characters
        summary_items = list((self.summary or {}).items())
        summary_lines = []
        for i, (key, value) in enumerate(summary_items):
            detail_is_last = i == len(summary_items) - 1
            detail_connector = "└─ " if detail_is_last else "├─ "
            summary_lines.append(
                detail_prefix + detail_connector + f"{key}: {str(value)}\n"
            )

        return node_header + "".join(summary_lines)

    def to_dict(self) -> dict:
        """Serialize this node to a JSON-compatible dictionary.

        Only the ``summary`` is included (not the raw ``data`` attribute).
        Non-finite floats become string representations (``"NaN"``,
        ``"Infinity"``, ``"-Infinity"``).  Other non-serializable values
        are converted via :func:`str`.

        Returns:
            dict: A JSON-serializable representation of this node.

        See Also:
            DataTree.to_json : Serialize the full result tree to JSON.
        """
        return {
            "type": "DataNode",
            "label": self.label,
            "_N": self._N,
            "summary": {
                k: _serialize_summary_value(v) for k, v in (self.summary or {}).items()
            },
        }

    def __flatten__(
        self,
        path=(),
        depth: int = 0,
        pivot_var=(),
        pivot_now: bool = False,
        path_pivot=(),
        pivot_split=(),
        pivot_lvl=(),
        data: bool = False,
    ) -> pd.DataFrame:

        path = path + ("analysis",)
        path_pivot = path_pivot + ("analysis",)

        return pd.DataFrame(
            {
                "type": ["analysis"],
                "split": [None],
                "lvl": [None],
                "path": [list(path)],
                "path_pivot": [list(path_pivot)],
                "pivot_split": [list(pivot_split)],
                "pivot_lvl": [list(pivot_lvl)],
                "depth": depth,
                "label": self.label,
                "summary": [self.data] if data else [self.summary],
            },
            index=[0],
        )


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

    def __str__(self, ind: int = 0, is_last: bool = True, prefix: str = ""):
        """Return a string representation of the split data node.

        Args:
            ind (int): Indentation level for nested display. Defaults to 0 (deprecated, use prefix).
            is_last (bool): Whether this is the last child of its parent. Defaults to True.
            prefix (str): The prefix string from parent levels. Defaults to "".

        Returns:
            str: Formatted representation of the split and its levels.
        """
        # Choose connector based on position
        connector = "└─ " if is_last else "├─ "
        split_str = prefix + connector + f"Split: {self.label}\n"

        # Build prefix for children
        child_prefix = prefix + ("   " if is_last else "│  ")

        # Process children
        result = [split_str]
        for i, child in enumerate(self.values()):
            child_is_last = i == len(self) - 1
            result.append(child.__str__(is_last=child_is_last, prefix=child_prefix))

        return "".join(result)

    def to_dict(self) -> dict:
        """Serialize this split node to a JSON-compatible dictionary.

        Returns:
            dict: A JSON-serializable representation of this node with keys
            ``type``, ``split_var``, ``label``, and ``children``.

        See Also:
            DataTree.to_json : Serialize the full result tree to JSON.
        """
        return {
            "type": "SplitDataNode",
            "split_var": self.split_var,
            "label": self.label,
            "children": {k: v.to_dict() for k, v in self.items()},
        }

    def __flatten__(
        self,
        path=(),
        depth: int = 0,
        pivot_var=(),
        path_pivot=(),
        pivot_split=(),
        pivot_lvl=(),
        data: bool = False,
    ) -> pd.DataFrame:

        path = path + (self.label,)  # split_var

        if self.label in pivot_var:
            path_pivot = path_pivot
            pivot_split = pivot_split + (self.label,)
            pivot_now = True

        else:
            path_pivot = path_pivot + (self.label,)
            pivot_now = False

        res_loc = pd.DataFrame(
            {
                "type": ["split"],
                "split": [self.label],
                "lvl": [None],
                "path": [list(path)],
                "path_pivot": [list(path_pivot)],
                "pivot_split": [list(pivot_split)],
                "pivot_lvl": [list(pivot_lvl)],
                "depth": depth,
                "summary": [None],
                "label": None,
            }
        )

        res = [
            x.__flatten__(
                path=path,
                depth=depth + 1,
                pivot_var=pivot_var,
                pivot_now=pivot_now,
                path_pivot=path_pivot,
                pivot_split=pivot_split,
                pivot_lvl=pivot_lvl,
                data=data,
            )
            for x in self.values()
        ]

        res = [res_loc] + res
        return pd.concat(res, ignore_index=True)


class LvlDataNode(dict):
    """A subclass of dictionnary that represents a hierarchical data node at a specific split level.

    Attributes:
        split_lvl (str): The identifier for the split level of this node.
        meta (any): Metadata associated with this node.
        _N (list | None): Cumulative unique-count list from root to current level when
            a denominator is set on the :class:`AnalysisTree`. ``None`` when no denominator
            is configured.
    """

    def __init__(
        self, split_lvl: str, meta: any = (), _N: list | None = None, **kwargs
    ):
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

        acceptable_lst = [
            isinstance(x, (SplitDataNode, DataNode)) for x in kwargs.values()
        ]
        assert all(acceptable_lst)

        assert isinstance(split_lvl, str)
        super().__init__(**kwargs)
        self.split_lvl = split_lvl
        self.meta = meta
        self._N = _N

    def __str__(self, ind: int = 0, is_last: bool = True, prefix: str = ""):
        """Return a string representation of the level data node.

        Args:
            ind (int): Indentation level for nested display. Defaults to 0 (deprecated, use prefix).
            is_last (bool): Whether this is the last child of its parent. Defaults to True.
            prefix (str): The prefix string from parent levels. Defaults to "".

        Returns:
            str: Formatted representation of the level and its children.
        """
        # Choose connector based on position
        connector = "└─ " if is_last else "├─ "
        level_str = prefix + connector + f"{self.split_lvl}\n"

        # Build prefix for children
        child_prefix = prefix + ("   " if is_last else "│  ")

        # Process children
        result = [level_str]
        for i, child in enumerate(self.values()):
            child_is_last = i == len(self) - 1
            result.append(child.__str__(is_last=child_is_last, prefix=child_prefix))

        return "".join(result)

    def to_dict(self) -> dict:
        """Serialize this level node to a JSON-compatible dictionary.

        Returns:
            dict: A JSON-serializable representation of this node with keys
            ``type``, ``split_lvl``, ``_N``, and ``children``.

        See Also:
            DataTree.to_json : Serialize the full result tree to JSON.
        """
        return {
            "type": "LvlDataNode",
            "split_lvl": self.split_lvl,
            "_N": self._N,
            "children": {k: v.to_dict() for k, v in self.items()},
        }

    def __flatten__(
        self,
        path=(),
        depth: int = 0,
        pivot_var=(),
        pivot_now: bool = False,
        path_pivot=(),
        pivot_split=(),
        pivot_lvl=(),
        data: bool = False,
    ) -> pd.DataFrame:
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
            path_pivot = path_pivot  # Do not add anything if pivoted.
            pivot_lvl = pivot_lvl + (self.split_lvl,)

        else:
            path_pivot = path_pivot + (self.split_lvl,)

        res_loc = pd.DataFrame(
            {
                "type": ["level"],
                "split": [None],
                "lvl": [self.split_lvl],
                "path": [list(path)],
                "path_pivot": [list(path_pivot)],
                "pivot_split": [list(pivot_split)],
                "pivot_lvl": [list(pivot_lvl)],
                "depth": depth,
                "label": None,
                "summary": [None],
            }
        )

        res = [
            x.__flatten__(
                path=path,
                depth=depth + 1,
                pivot_var=pivot_var,
                path_pivot=path_pivot,
                pivot_split=pivot_split,
                pivot_lvl=pivot_lvl,
                data=data,
            )
            for x in self.values()
        ]
        res = [res_loc] + res
        return pd.concat(res, ignore_index=True)


class DataTree(dict):
    """A subclass of dictionnary that represents a data tree.

    Attributes:
        _N (list | None): Cumulative unique-count list; a single-element list ``[n_root]``
            when a denominator is set on the :class:`AnalysisTree`. ``None`` when no
            denominator is configured.
    """

    def __init__(self, _N: list | None = None, **kwargs):
        """Initializes the DataTree object.
        Args:
            _N (int, optional): The number of unique identifiers in the data, if applicable. Defaults to None.
            **kwargs: Keyword arguments where each value must be an instance of SplitDataNode or DataNode.
        Raises:
            AssertionError: If any value in kwargs is not an instance of SplitDataNode or Data
        Examples:
            >>> DataTree()
        """
        acceptable_lst = [
            isinstance(x, (SplitDataNode, DataNode)) for x in kwargs.values()
        ]
        assert all(acceptable_lst)
        super().__init__(**kwargs)
        self._N = _N

    def __str__(self):
        """Return a string representation of the data tree.

        Returns:
            str: Formatted tree structure showing splits, levels, and results.
        """
        if len(self) == 0:
            return "Data Tree\n"

        result = ["Data Tree\n"]
        for i, node in enumerate(self.values()):
            is_last = i == len(self) - 1
            result.append(node.__str__(is_last=is_last, prefix=""))
        return "".join(result)

    def to_dict(self) -> dict:
        """Serialize the result tree to a JSON-compatible dictionary.

        The dictionary captures the full hierarchical result structure,
        including every split, level, and analysis node with its computed
        summary statistics.  Raw data (``DataNode.data``) is intentionally
        excluded to keep the output concise and suitable for LLM consumption.

        Non-finite float values in any summary dictionary are converted to
        string representations (``"NaN"``, ``"Infinity"``, ``"-Infinity"``).
        Other non-serializable objects are converted via :func:`str`.

        Returns:
            dict: A JSON-serializable representation of the result tree with
            keys ``type``, ``_N``, and ``children``.

        See Also:
            to_json : Serialize to a JSON string (optionally writing to a file).

        Examples:
            >>> import numpy as np, pandas as pd
            >>> from pyMyriad import AnalysisTree
            >>> df = pd.DataFrame({"A": [1, 2, 3], "G": ["M", "F", "M"]})
            >>> result = AnalysisTree().split_by("df.G").analyze_by(n="len(df)").run(df, environ={"np": np})
            >>> d = result.to_dict()
            >>> d["type"]
            'DataTree'
        """
        return {
            "type": "DataTree",
            "_N": self._N,
            "children": {k: v.to_dict() for k, v in self.items()},
        }

    def to_json(self, path: str = None, indent: int = 2) -> str:
        """Serialize the result tree to a JSON string.

        Produces a human-readable JSON representation of all analysis
        results, suitable for sharing with LLM agents or storing alongside
        an analysis plan.  The JSON structure mirrors the tree hierarchy:
        splits, levels, and analysis nodes with their computed statistics.

        Args:
            path (str, optional): If provided, the JSON is also written to
                this file.  The directory must already exist.
                Defaults to ``None``.
            indent (int, optional): Number of spaces used for indentation.
                Defaults to ``2``.

        Returns:
            str: The JSON string representation of the result tree.

        See Also:
            to_dict : Serialize to a plain Python dictionary.
            AnalysisTree.to_json : Serialize the *analysis plan* (not results).

        Examples:
            >>> import numpy as np, pandas as pd
            >>> from pyMyriad import AnalysisTree
            >>> df = pd.DataFrame({"A": [1, 2, 3], "G": ["M", "F", "M"]})
            >>> result = AnalysisTree().split_by("df.G").analyze_by(n="len(df)").run(df, environ={"np": np})
            >>> json_str = result.to_json()
            >>> import json; parsed = json.loads(json_str)
            >>> parsed["type"]
            'DataTree'
        """
        result = json.dumps(self.to_dict(), indent=indent)
        if path is not None:
            with open(path, "w", encoding="utf-8") as f:
                f.write(result)
        return result

    def __flatten__(self, pivot: str = (), data: bool = False) -> pd.DataFrame:
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

        res_loc = pd.DataFrame(
            {
                "type": ["root"],
                "split": [None],
                "lvl": [None],
                "path": [list(path)],
                "path_pivot": [list(path)],
                "pivot_split": [list(())],
                "pivot_lvl": [list(())],
                "depth": depth,
                "label": None,
                "summary": [None],
            }
        )

        res = [
            x.__flatten__(
                path=path,
                depth=depth + 1,
                pivot_var=pivot,
                path_pivot=path_pivot,
                pivot_split=pivot_split,
                pivot_lvl=pivot_lvl,
                data=data,
            )
            for x in self.values()
        ]
        res = [res_loc] + res
        return pd.concat(res, ignore_index=True)

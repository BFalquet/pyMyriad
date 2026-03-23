"""Tabular data flattening and formatting module.

This module provides functions for converting DataTree objects into pandas
DataFrames and formatting statistics for presentation.

Key functions:
- tabulate(): Flatten a DataTree with summary statistics
- flatten_data(): Flatten a DataTree including raw data
- format_statistics(): Apply format strings to statistical summaries
- flatten(): Alias for tabulate()

Example:
    >>> from pyMyriad import AnalysisTree, format_statistics
    >>> from pyMyriad.tabular import tabulate, flatten
    >>>
    >>> # Run analysis
    >>> tree = AnalysisTree().split_by('df.Gender').analyze_by(
    ...     mean=lambda df: np.mean(df.Income),
    ...     std=lambda df: np.std(df.Income)
    ... )
    >>> result = tree.run(df)
    >>>
    >>> # Flatten to DataFrame
    >>> table = tabulate(result, unnest=True)
    >>> print(table)
    >>>
    >>> # Format statistics
    >>> formatted = format_statistics(result, summary="{mean:.2f}±{std:.2f}")

See also:
    - examples/03_tables_and_listings.ipynb: Table generation examples
    - examples/05_formatting_statistics.ipynb: Formatting examples
    - listing.py: User-facing table generation functions
"""

from .data_tree import DataNode, SplitDataNode, DataTree
import pandas as pd


def tabulate(dtree: DataTree, unnest: bool = False, pivot: str = ()) -> pd.DataFrame:
    """Tabulates a DataTree into a DataFrame.

    Args:
        dtree (DataTree): The DataTree to flatten.
        unnest (bool, optional): If True, unnests the 'summary' column if it contains lists or dictionaries. Defaults to False.
        pivot (str, optional): the name of a split to pivot by.
    Returns:
        pd.DataFrame: A flattened representation of the DataTree.
    Examples:
        >>> dtree = DataTree(
        ...     s = SplitDataNode(
        ...         split_var="VAR",
        ...         node=LvlDataNode(
        ...             split_lvl="lvl1",
        ...             group1=DataNode(
        ...                 label="Group 1",
        ...                 summary={"mean_val": 10, "count": 5}
        ...             ),
        ...             group2=DataNode(
        ...                 label="Group 2",
        ...                 summary={"mean_val": 100, "count": 50}
        ...             )
        ...         ),
        ...         node2=LvlDataNode(
        ...             split_lvl="lvl2",
        ...             group1=DataNode(
        ...                 label="Group 1",
        ...                 summary={"mean_val": 8, "count": 9}
        ...             ),
        ...             group2=DataNode(
        ...                 label="Group 2",
        ...                 summary={"mean_val": 88, "count": 99}
        ...             )
        ...         )
        ...     ),
        ...     a = DataNode(
        ...         label="Overall",
        ...         summary={"mean_val": 15, "count": 8}
        ...     )
        ... )
        >>> tabulate(dtree, unnest=True)
    """

    assert isinstance(dtree, DataTree)
    assert isinstance(pivot, str)

    flat_df = dtree.__flatten__(pivot=pivot).reset_index(drop=True)

    if unnest:
        df_value = pd.DataFrame()
        df_value["statistics"] = flat_df["summary"].apply(
            lambda x: x.keys() if isinstance(x, dict) else None
        )
        df_value["values"] = flat_df["summary"].apply(
            lambda x: x.values() if isinstance(x, dict) else None
        )
        df_value = df_value.explode(column=["statistics", "values"])
        flat_df = flat_df.drop(columns="summary").join(df_value, how="left")

    if len(pivot) > 0 and unnest:
        flat_df["path_pivot"] = flat_df["path_pivot"].apply(
            lambda x: "None" if x is None else " > ".join(x)
        )
        flat_df["pivot_lvl"] = flat_df["pivot_lvl"].apply(
            lambda x: "None" if x is None else " > ".join(x)
        )

        flat_df = flat_df.pivot(
            index=["path_pivot", "type", "statistics", "label"],
            columns="pivot_lvl",
            values="values",
        ).reset_index()

    elif len(pivot) > 0 and not unnest:
        flat_df["path_pivot"] = flat_df["path_pivot"].apply(
            lambda x: "None" if x is None else " > ".join(x)
        )
        flat_df["pivot_lvl"] = flat_df["pivot_lvl"].apply(
            lambda x: "None" if x is None else " > ".join(x)
        )

        flat_df = flat_df.pivot(
            index=["path_pivot", "type", "label"], columns="pivot_lvl", values="summary"
        ).reset_index()

    return flat_df


def flatten(dtree: DataTree, unnest: bool = False, by: str = ()) -> pd.DataFrame:
    """Flattens a DataTree into a Long DataFrame.

    Args:
        dtree (DataTree): The DataTree to flatten.
        unnest (bool, optional): If True, unnests the 'summary' column if it contains lists or dictionaries. Defaults to False.
        pivot (str, optional): the name of a split to pivot by.
    Returns:
        pd.DataFrame: A flattened representation of the DataTree.
    Examples:
        >>> dtree = DataTree(
        ...     s = SplitDataNode(
        ...         split_var="VAR",
        ...         node=LvlDataNode(
        ...             split_lvl="lvl1",
        ...             group1=DataNode(
        ...                 label="Group 1",
        ...                 summary={"mean_val": 10, "count": 5}
        ...             ),
        ...             group2=DataNode(
        ...                 label="Group 2",
        ...                 summary={"mean_val": 100, "count": 50}
        ...             )
        ...         ),
        ...         node2=LvlDataNode(
        ...             split_lvl="lvl2",
        ...             group1=DataNode(
        ...                 label="Group 1",
        ...                 summary={"mean_val": 8, "count": 9}
        ...             ),
        ...             group2=DataNode(
        ...                 label="Group 2",
        ...                 summary={"mean_val": 88, "count": 99}
        ...             )
        ...         )
        ...     ),
        ...     a = DataNode(
        ...         label="Overall",
        ...         summary={"mean_val": 15, "count": 8}
        ...     )
        ... )
        >>> flatten(dtree, unnest=True)
    """

    flat_df = dtree.__flatten__(pivot=by).reset_index(drop=True)

    if unnest:
        df_value = pd.DataFrame()
        df_value["statistics"] = flat_df["summary"].apply(
            lambda x: x.keys() if isinstance(x, dict) else None
        )
        df_value["values"] = flat_df["summary"].apply(
            lambda x: x.values() if isinstance(x, dict) else None
        )
        df_value = df_value.explode(column=["statistics", "values"])
        flat_df = flat_df.drop(columns="summary").join(df_value, how="left")

    return flat_df


def flatten_data(dtree: DataTree, unnest: bool = False, by: str = ()) -> pd.DataFrame:
    """Flatten a DataTree including raw data from DataNodes.

    Similar to tabulate() but preserves the raw data stored in DataNode objects
    instead of just extracting summary statistics.

    Args:
        dtree (DataTree): The DataTree to flatten with raw data.
        unnest (bool, optional): Currently unused for data flattening. Defaults to False.
        by (str, optional): The name of a split to pivot by. Defaults to ().

    Returns:
        pd.DataFrame: A flattened representation of the DataTree including raw data.

    Examples:
        >>> tree = AnalysisTree().split_by('df.Gender').analyze_by(
        ...     data=lambda df: df[['Income', 'Age']]
        ... )
        >>> result = tree.run(df)
        >>> flat_df = flatten_data(result)
        >>> # flat_df contains the raw data organized by the tree structure

        >>> # With pivot
        >>> flat_df = flatten_data(result, by='df.Gender')

    See Also:
        tabulate : Flatten DataTree with summary statistics only.
    """
    flat_df = dtree.__flatten__(pivot=by, data=True).reset_index(drop=True)

    return flat_df


def format_statistics(
    dtree: DataTree,
    label=None,
    remove_original: bool = False,
    inplace: bool = False,
    safe: bool = False,
    **kwargs,
):
    """Formats statistics in DataNode objects according to format specifications.

    This function creates new formatted statistics by combining existing statistics
    according to format strings. By default, returns a modified copy of the tree.

    Args:
        dtree (DataTree): The DataTree to format.
        label (str, optional): If specified, only applies formatting to DataNodes with this label.
            If None (default), applies formatting to all DataNodes.
        remove_original (bool, optional): If True, removes the original statistics
            that were used in the format strings, keeping only the formatted results.
            Defaults to False.
        inplace (bool, optional): If True, modifies the DataTree in place. If False,
            creates and returns a modified copy, leaving the original unchanged.
            Defaults to False.
        safe (bool, optional): If True, raises an error when formatting fails. If False,
            silently skips nodes where formatting fails and prints a warning message.
            Defaults to False.
        **kwargs: Keyword arguments where keys are the new statistic names and values
            are format strings. Example: mean_sd="{m} +/- {sd}"

    Returns:
        DataTree: The modified DataTree. If inplace=True, returns the same object.
            If inplace=False, returns a new modified copy.

    Raises:
        ValueError: If no format specifications are provided in kwargs.
        KeyError: If safe=True and a format string references a statistic that doesn't exist.

    Examples:
        # Apply format to all nodes
        >>> dtree = DataTree(
        ...     a = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}),
        ...     b = DataNode(label="Median", summary={"m": 12.0, "sd": 3.1})
        ... )
        >>> new_dtree = format_statistics(dtree, mean_sd="{m} +/- {sd}")
        # Both nodes get the "mean_sd" statistic

        # Apply format only to specific label
        >>> new_dtree = format_statistics(dtree, label="Mean", result="{m} ± {sd}")
        # Only the node with label="Mean" gets the "result" statistic

        # Multiple formats applied to all nodes
        >>> new_dtree = format_statistics(
        ...     dtree,
        ...     mean_sd="{m:.1f} +/- {sd:.1f}",
        ...     mean_only="{m:.2f}",
        ...     inplace=True
        ... )

        # Remove original statistics after formatting
        >>> new_dtree = format_statistics(
        ...     dtree,
        ...     formatted="{m} +/- {sd}",
        ...     remove_original=True
        ... )
    """

    if not kwargs:
        raise ValueError(
            "At least one format specification must be provided as a keyword argument"
        )

    # Create a deep copy if not modifying in place
    if not inplace:
        import copy

        dtree = copy.deepcopy(dtree)

    def _apply_format_to_node(node):
        """Recursively apply formatting to DataNode objects."""
        if isinstance(node, DataNode):
            if node.summary is not None:
                # Check if we should apply formatting to this node
                if label is None or node.label == label:
                    # Apply each format specification
                    for stat_name, format_string in kwargs.items():
                        try:
                            formatted_value = format_string.format(**node.summary)

                            if remove_original:
                                # Extract the keys used in this format string
                                import re

                                # Find all {key} or {key:format} patterns
                                pattern = r"\{([^}:]+)(?::[^}]*)?\}"
                                keys_used = set(re.findall(pattern, format_string))

                                # Remove the used keys from summary
                                for key in keys_used:
                                    node.summary.pop(key, None)

                            # Add the formatted statistic
                            node.summary[stat_name] = formatted_value

                        except KeyError as e:
                            if safe:
                                raise KeyError(
                                    f"Format string for '{stat_name}' references non-existent statistic {e} in node '{node.label}'. Available statistics: {list(node.summary.keys())}"
                                )
                            else:
                                print(
                                    f"Warning: Format string for '{stat_name}' references non-existent statistic {e} in node '{node.label}'. Available statistics: {list(node.summary.keys())}. Skipping this node."
                                )

        elif isinstance(node, (SplitDataNode, dict)):
            # Recursively process child nodes
            for child in node.values():
                _apply_format_to_node(child)

    # Apply formatting to all nodes in the tree
    for node in dtree.values():
        _apply_format_to_node(node)

    return dtree

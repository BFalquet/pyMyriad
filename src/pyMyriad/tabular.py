from .data_tree import DataNode, SplitDataNode, LvlDataNode, DataTree
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
        dtree = DataTree(
            s = SplitDataNode(
                split_var="VAR",
                node=LvlDataNode(
                    split_lvl="lvl1",
                    group1=DataNode(
                        label="Group 1",
                        summary={"mean_val": 10, "count": 5}
                    ),
                    group2=DataNode(
                        label="Group 2",
                        summary={"mean_val": 100, "count": 50}
                    )
                ),
                node2=LvlDataNode(
                    split_lvl="lvl2",
                    group1=DataNode(
                        label="Group 1",
                        summary={"mean_val": 8, "count": 9}
                    ),
                    group2=DataNode(
                        label="Group 2",
                        summary={"mean_val": 88, "count": 99}
                    )
                )
            ),
            a = DataNode(
                label="Overall",
                summary={"mean_val": 15, "count": 8}
            )
        )
        tabulate(dtree, unnest=True)
    """

    assert isinstance(dtree, DataTree)
    assert isinstance(pivot, str)

    flat_df = dtree.__flatten__(pivot = pivot).reset_index(drop = True)

    if unnest:
        df_value = pd.DataFrame()
        df_value['statistics'] = flat_df['summary'].apply(lambda x: x.keys() if isinstance(x, dict) else None)
        df_value['values'] = flat_df['summary'].apply(lambda x: x.values() if isinstance(x, dict) else None)
        df_value = df_value.explode(column = ['statistics', 'values'])
        flat_df = flat_df.drop(columns = 'summary').join(df_value, how = "left")


    if len(pivot) > 0 and unnest:
        flat_df['path_pivot'] = flat_df['path_pivot'].apply(lambda x: "None" if x is None else " > ".join(x))
        flat_df['pivot_lvl'] = flat_df['pivot_lvl'].apply(lambda x: "None" if x is None else " > ".join(x))

        flat_df = flat_df.pivot(
            index = ['path_pivot', 'type', 'statistics', 'label'],
            columns = 'pivot_lvl',
            values = 'values'
        ).reset_index()

    elif len(pivot) > 0 and not unnest:
        flat_df['path_pivot'] = flat_df['path_pivot'].apply(lambda x: "None" if x is None else " > ".join(x))
        flat_df['pivot_lvl'] = flat_df['pivot_lvl'].apply(lambda x: "None" if x is None else " > ".join(x))

        flat_df = flat_df.pivot(
            index = ['path_pivot', 'type', 'label'],
            columns = 'pivot_lvl',
            values = 'summary'
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
        dtree = DataTree(
            s = SplitDataNode(
                split_var="VAR",
                node=LvlDataNode(
                    split_lvl="lvl1",
                    group1=DataNode(
                        label="Group 1",
                        summary={"mean_val": 10, "count": 5}
                    ),
                    group2=DataNode(
                        label="Group 2",
                        summary={"mean_val": 100, "count": 50}
                    )
                ),
                node2=LvlDataNode(
                    split_lvl="lvl2",
                    group1=DataNode(
                        label="Group 1",
                        summary={"mean_val": 8, "count": 9}
                    ),
                    group2=DataNode(
                        label="Group 2",
                        summary={"mean_val": 88, "count": 99}
                    )
                )
            ),
            a = DataNode(
                label="Overall",
                summary={"mean_val": 15, "count": 8}
            )
        )
        flatten(dtree, unnest=True)
    """

    flat_df = dtree.__flatten__(pivot = by).reset_index(drop = True)

    if unnest:
        df_value = pd.DataFrame()
        df_value['statistics'] = flat_df['summary'].apply(lambda x: x.keys() if isinstance(x, dict) else None)
        df_value['values'] = flat_df['summary'].apply(lambda x: x.values() if isinstance(x, dict) else None)
        df_value = df_value.explode(column = ['statistics', 'values'])
        flat_df = flat_df.drop(columns = 'summary').join(df_value, how = "left")

    return flat_df

def flatten_data(dtree: DataTree, unnest: bool = False, by: str = ()) -> pd.DataFrame:
    flat_df = dtree.__flatten__(pivot = by, data = True).reset_index(drop = True)

    return flat_df


def format_statistics(dtree: DataTree, format_spec=None, format_map: dict = None, stat_name: str = "formatted", remove_original: bool = False, inplace: bool = False):
    """Formats statistics in DataNode objects according to a format specification.
    
    This function creates a new formatted statistic by combining existing statistics
    according to a format string. By default, returns a modified copy of the tree.
    
    Args:
        dtree (DataTree): The DataTree to format.
        format_spec (str, optional): A global format string to apply to all DataNodes.
            Example: "{m} +/- {sd}" will combine 'm' and 'sd' statistics.
        format_map (dict, optional): A dictionary mapping labels to format strings,
            allowing different formats for different nodes.
            Example: {"Mean": "{m} +/- {sd}", "Median": "{median} [{q1}-{q3}]"}
        stat_name (str, optional): The name of the new formatted statistic.
            Defaults to "formatted".
        remove_original (bool, optional): If True, removes the original statistics
            that were used in the format string, keeping only the formatted result.
            Defaults to False.
        inplace (bool, optional): If True, modifies the DataTree in place. If False,
            creates and returns a modified copy, leaving the original unchanged.
            Defaults to False.
    
    Returns:
        DataTree: The modified DataTree. If inplace=True, returns the same object.
            If inplace=False, returns a new modified copy.
    
    Raises:
        ValueError: If neither format_spec nor format_map is provided.
        KeyError: If a format string references a statistic that doesn't exist.
    
    Examples:
        # Default behavior - returns a new copy
        dtree = DataTree(
            a = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3})
        )
        new_dtree = format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="result")
        # dtree is unchanged, new_dtree has the formatted statistic
        
        # Modify in place
        format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="result", inplace=True)
        # dtree is now modified
        
        # Remove original statistics after formatting
        new_dtree = format_statistics(dtree, format_spec="{m} +/- {sd}", stat_name="result", remove_original=True)
        # new_dtree["a"].summary contains only {"result": "10.5 +/- 2.3"}
        
        # Different formats for different labels
        dtree = DataTree(
            mean_node = DataNode(label="Mean", summary={"m": 10.5, "sd": 2.3}),
            median_node = DataNode(label="Median", summary={"median": 11, "q1": 9, "q3": 13})
        )
        new_dtree = format_statistics(
            dtree, 
            format_map={"Mean": "{m} +/- {sd}", "Median": "{median} [{q1}-{q3}]"},
            stat_name="summary_text"
        )
    """
    
    if format_spec is None and format_map is None:
        raise ValueError("Either format_spec or format_map must be provided")
    
    # Create a deep copy if not modifying in place
    if not inplace:
        import copy
        dtree = copy.deepcopy(dtree)
    
    def _apply_format_to_node(node):
        """Recursively apply formatting to DataNode objects."""
        if isinstance(node, DataNode):
            if node.summary is not None:
                # Determine which format to use
                if format_map is not None and node.label in format_map:
                    fmt = format_map[node.label]
                elif format_spec is not None:
                    fmt = format_spec
                else:
                    # No format applies to this node
                    return
                
                # Try to format using the statistics in summary
                try:
                    formatted_value = fmt.format(**node.summary)
                    
                    if remove_original:
                        # Extract the keys used in the format string
                        import re
                        # Find all {key} or {key:format} patterns
                        pattern = r'\{([^}:]+)(?::[^}]*)?\}'
                        keys_used = set(re.findall(pattern, fmt))
                        
                        # Create new summary with only the formatted result and unused stats
                        new_summary = {k: v for k, v in node.summary.items() if k not in keys_used}
                        new_summary[stat_name] = formatted_value
                        node.summary = new_summary
                    else:
                        node.summary[stat_name] = formatted_value
                        
                except KeyError as e:
                    raise KeyError(f"Format string references non-existent statistic {e} in node '{node.label}'. Available statistics: {list(node.summary.keys())}")
        
        elif isinstance(node, (SplitDataNode, dict)):
            # Recursively process child nodes
            for child in node.values():
                _apply_format_to_node(child)
    
    # Apply formatting to all nodes in the tree
    for node in dtree.values():
        _apply_format_to_node(node)
    
    return dtree
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
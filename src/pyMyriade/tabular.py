from .data_tree import DataNode, SplitDataNode, DataTree
import pandas as pd

def flatten(dtree: DataTree, unnest: bool = False) -> pd.DataFrame:
    """Flattens a DataTree into a DataFrame.

    Args:
        dtree (DataTree): The DataTree to flatten.
        unnest (bool, optional): If True, unnests the 'summary' column if it contains lists or dictionaries. Defaults to False.
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
                        summary={"mean_val": 20, "count": 3}
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
    flat_df = dtree.__flatten__().reset_index(drop = True)

    if unnest:
        df_value = pd.DataFrame()
        df_value['statistics'] = flat_df['summary'].apply(lambda x: x.keys() if isinstance(x, dict) else None)
        df_value['values'] = flat_df['summary'].apply(lambda x: x.values() if isinstance(x, dict) else None)
        df_value = df_value.explode(column = ['statistics', 'values'])
        
        return flat_df.drop(columns = 'summary').join(df_value, how = "left")

    else:
        return flat_df

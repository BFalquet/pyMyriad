from .tabular import flatten, flatten_data
import pandas as pd
import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# import plotly.io as pio

import matplotlib.pyplot as plt
import seaborn as sns

def forest_plot(dtree, type:str="forest", x:str = "x", x_err:str = "err", col:str = (), jitter:bool = False, show = True):
    """Create a forest plot from a DataTree object.

    Args:
        dtree (DataTree): The DataTree object containing the analysis results.
        type (str, optional): The type of plot to create. Currently only "forest" is supported. Defaults to "forest".
        x (str, optional): The column name for the x-axis values. Defaults to "x".
        x_err (str, optional): The column name for the x-axis error values. Defaults to "err".
        col (str or list of str, optional): Column(s) to facet the plot by. Defaults to ().
        jitter (bool, optional): Whether to apply jittering to the y-axis positions to avoid overplotting. Defaults to False.
        show (bool, optional): Whether to display the plot immediately. If False, returns the figure object. Defaults to True.

    Examples:

    """

    res = flatten(dtree, unnest=True, by = col)

    # Preprocess to allow pivot
    res['pivot_lvl'] = res['pivot_lvl'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['pivot_split'] = res['pivot_split'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['label'] = res.apply(lambda row: "__not__analysis__" if (row["type"] != "analysis") else row["label"], axis = 1)
    res['label'] = res['label'].apply(lambda x: "Unlabelled" if len(x) == 0 else x) # 0 len label make pivot delete the corresponding lines.

    # Remove the last element from path_pivot for y_label
    res['y_label'] = res.apply(lambda row: str(row['path_pivot'][-2]) if row['type'] == "analysis" else row['lvl'] or row['split'] or "Overall", axis=1)

    # Remove unnecessary rows
    available_analysis = res.loc[res['type'] == "analysis", 'path_pivot'].apply(lambda x: x[:-1])
    available_analysis = available_analysis.apply(lambda x: " >> ".join(x)).unique()
    res['path_pivot'] = res['path_pivot'].apply(lambda x: " >> ".join(x))
    res = res.loc[~(res['path_pivot'].isin(available_analysis) & (res['type'] != "analysis"))]

    res = res.reset_index().rename(columns={'index': '_id'})

    res = res.pivot(
       index = ["_id", "depth", "split", "type", "path_pivot", "pivot_lvl", "pivot_split", "label", "y_label"], # y
       columns = "statistics",
       values = "values"
    )

    # Reset index so 'index' becomes a column again.
    res = res.reset_index()

    # Find the rank if the values in the y columns
    # - "dense" is not working because it is not respecting alphabetic order.
    # - "first" is not working because we need dense.
    rank_dict = {p: -i for i, p in enumerate(res.loc[~res['path_pivot'].duplicated(), 'path_pivot'])}
    res['y'] = res['path_pivot'].map(rank_dict)

    res['y_label'] = res.apply(lambda row: (" " * row['depth'] * 2) + row['y_label'], axis=1)

    # TODO: remove the split to the top left
    # TODO: add color map to the side of the plot if col is not None
    # TODO: add assertion on the presence of x and x_err

    # remove rows that are not analysis from data but keep the data frame for y_label calculation
    res_data = res.loc[res["label"] != '__not__analysis__', :].copy()

    # introducing jittering based on colour
    if ((len(res_data['pivot_lvl'].unique()) > 1) & jitter):
        print("Jittering")
        codes = pd.Categorical(res_data['pivot_lvl']).codes
        # min max normalization to [-0.3, +0.3]
        norm_codes = (codes - np.min(codes)) / (np.max(codes) - np.min(codes)) * 0.4 - 0.2
        res_data["y_jitter"] = res_data["y"] + norm_codes
    else:
        res_data["y_jitter"] = res_data["y"]

    g = sns.FacetGrid(res_data, col="label", hue = "pivot_lvl", sharey=True, sharex=False)
    g.map_dataframe(plot_1d, type = type, x = x, x_err = x_err)
    max_label_len = np.max(res['y_label'].apply(len))
 
    # First invert the y-axis, then set the ticks
    def set_ticks(data, **kwargs):
        ax = plt.gca()  # Gets the current axis for the facet
        ax.set_yticks(ticks=res['y'], labels=res['y_label'])  # Use 'res' not 'data'
        ax.tick_params(axis='y', which='major', labelsize='medium', pad=max_label_len * 5)
        ax.yaxis.set_tick_params(labelleft=True, labelright=False)
        for tick in ax.get_yticklabels():
            tick.set_horizontalalignment('left')

    g.map_dataframe(set_ticks)

    # Avoid repeating the y-axis labels for each plot
    for i, ax in enumerate(g.axes.flat):
        if i != 0:  # If not the first column
            ax.tick_params(labelleft=False)
            ax.set_ylabel("")

    plt.subplots_adjust(wspace=0.2)
    plt.show()


def plot_1d(data, type:str = "forest", x:str = "x", x_err:str = "err", **kwargs):
    """Create a 1D plot.

    Args:
        type (str, optional): The type of plot to create. Currently supports "forest", "range", "bar", "point".
        x (str, optional): The column name for the x-axis values. Defaults to "x".
        x_err (str, optional): The column name for the x-axis error values. Defaults to "err".

    Examples:

    """
    y = "y_jitter"

    if type == "forest":
            plt.errorbar(
                data[x], 
                data[y],
                xerr=data[x_err], 
                marker='o', 
                linestyle=''
            )

    elif type == "range":
            plt.errorbar(
                data[x], 
                data[y],
                xerr=data[x_err], 
                marker='', 
                linestyle=''
            )
    
    elif type == "point":
            plt.scatter(
                data[x], 
                data[y],
                marker='o'
            )

    elif type == "bar":
            plt.barh(
                y = data[y],
                width = data[x],
                height = 0.4
            )

    else:
        raise ValueError(f"Unknown plot type: {type}")
    



def distribution_plot(dtree, type:str="forest", x:str = "x", x_err:str = "err", col:str = (), jitter:bool = False, show = True):
    """Create a forest plot from a DataTree object.

    Args:
        dtree (DataTree): The DataTree object containing the analysis results.
        type (str, optional): The type of plot to create. Currently only "forest" is supported. Defaults to "forest".
        x (str, optional): The column name for the x-axis values. Defaults to "x".
        x_err (str, optional): The column name for the x-axis error values. Defaults to "err".
        col (str or list of str, optional): Column(s) to facet the plot by. Defaults to ().
        jitter (bool, optional): Whether to apply jittering to the y-axis positions to avoid overplotting. Defaults to False.
        show (bool, optional): Whether to display the plot immediately. If False, returns the figure object. Defaults to True.

    Examples:

    """

    res = flatten_data(dtree, unnest=False, by = col)

    # Preprocess to allow pivot
    res['pivot_lvl'] = res['pivot_lvl'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['pivot_split'] = res['pivot_split'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['label'] = res.apply(lambda row: "__not__analysis__" if (row["type"] != "analysis") else row["label"], axis = 1)
    res['label'] = res['label'].apply(lambda x: "Unlabelled" if len(x) == 0 else x) # 0 len label make pivot delete the corresponding lines.

    # Remove the last element from path_pivot for y_label
    res['y_label'] = res.apply(lambda row: str(row['path_pivot'][-2]) if row['type'] == "analysis" else row['lvl'] or row['split'] or "Overall", axis=1)

    # Remove unnecessary rows
    available_analysis = res.loc[res['type'] == "analysis", 'path_pivot'].apply(lambda x: x[:-1])
    available_analysis = available_analysis.apply(lambda x: " >> ".join(x)).unique()
    res['path_pivot'] = res['path_pivot'].apply(lambda x: " >> ".join(x))
    res = res.loc[~(res['path_pivot'].isin(available_analysis) & (res['type'] != "analysis"))]

    res = res.reset_index().rename(columns={'index': '_id'})

    # res = res.pivot(
    #    index = ["_id", "depth", "split", "type", "path_pivot", "pivot_lvl", "pivot_split", "label", "y_label"], # y
    #    columns = "summary", # keep data in one column
    #    values = "values"
    # )

    # Reset index so 'index' becomes a column again.
    # res = res.reset_index()

    # Find the rank if the values in the y columns
    # - "dense" is not working because it is not respecting alphabetic order.
    # - "first" is not working because we need dense.
    rank_dict = {p: -i for i, p in enumerate(res.loc[~res['path_pivot'].duplicated(), 'path_pivot'])}
    res['y'] = res['path_pivot'].map(rank_dict)

    res['y_label'] = res.apply(lambda row: (" " * row['depth'] * 2) + row['y_label'], axis=1)

    # TODO: remove the split to the top left
    # TODO: add color map to the side of the plot if col is not None
    # TODO: add assertion on the presence of x and x_err

    # remove rows that are not analysis from data but keep the data frame for y_label calculation
    res_data = res.loc[res["label"] != '__not__analysis__', :].copy()

    # introducing jittering based on colour
    if ((len(res_data['pivot_lvl'].unique()) > 1) & jitter):
        print("Jittering")
        codes = pd.Categorical(res_data['pivot_lvl']).codes
        # min max normalization to [-0.3, +0.3]
        norm_codes = (codes - np.min(codes)) / (np.max(codes) - np.min(codes)) * 0.4 - 0.2
        res_data["y_jitter"] = res_data["y"] + norm_codes
    else:
        res_data["y_jitter"] = res_data["y"]

    g = sns.FacetGrid(res_data, col="label", hue = "pivot_lvl", sharey=True, sharex=False)
    g.map_dataframe(plot_distribution, type = type, x = x)
    max_label_len = np.max(res['y_label'].apply(len))
 
    # First invert the y-axis, then set the ticks
    def set_ticks(data, **kwargs):
        ax = plt.gca()  # Gets the current axis for the facet
        ax.set_yticks(ticks=res['y'], labels=res['y_label'])  # Use 'res' not 'data'
        ax.tick_params(axis='y', which='major', labelsize='medium', pad=max_label_len * 5)
        ax.yaxis.set_tick_params(labelleft=True, labelright=False)
        for tick in ax.get_yticklabels():
            tick.set_horizontalalignment('left')

    g.map_dataframe(set_ticks)

    # Avoid repeating the y-axis labels for each plot
    for i, ax in enumerate(g.axes.flat):
        if i != 0:  # If not the first column
            ax.tick_params(labelleft=False)
            ax.set_ylabel("")

    plt.subplots_adjust(wspace=0.2)
    plt.show()

def plot_distribution(data, type:str = "scatter", x:str = "x", x_err:str = "err", **kwargs):
    """Create a 1D plot.

    Args:
        type (str, optional): The type of plot to create. Currently supports "forest", "range", "bar", "point".
        x (str, optional): The column name for the x-axis values. Defaults to "x".
        x_err (str, optional): The column name for the x-axis error values. Defaults to "err".

    Examples:

    """
    y = "y"

    # The data are nested in a data frame in the "summary" column.
    x_series = data["summary"]
    assert x in x_series.iloc[0].columns, f"{x} not found in the data, available columns: {x_series.iloc[0].columns.tolist()}"
    x_series = x_series.apply(lambda row: list(row[x])).explode()

    y_series = data[[y]]
    merge_data = pd.merge(y_series, x_series, left_index=True, right_index=True, how='left')
    merge_data = merge_data.rename(columns={"summary": x})

    # y_lab = data["y_label"].to_list()

    if type == "forest":
        plt.scatter(
            merge_data[x], 
            merge_data[y],
            marker='o',
            linestyle=''
        )

    elif type == "boxplot":
            
        # merge_data_list = merge_data.groupby(y)[x].apply(list)
        # y_positions = merge_data_list.index.tolist()
    
        # box = plt.boxplot(
        #     x = merge_data_list,
        #     positions = y_positions,
        #     orientation='horizontal',
        #     widths = 0.15
        # )

        sns.boxplot(
            x = x,
            y = y,
            data = merge_data,
            orient = 'h',
            dodge=True,
            order= merge_data[y].unique()
        )



    else:
        raise ValueError(f"Unknown plot type: {type}")
    

"""Visualization module.

This module provides functions for creating publication-ready plots from DataTree
analysis results.

Main plotting functions:
- forest_plot(): Create forest plots for effect sizes and confidence intervals
- distribution_plot(): Create distribution plots showing raw data

Helper functions:
- plot_1d(): Internal function for 1D plot types
- plot_distribution(): Internal function for distribution plot rendering

Example:
    >>> from pyMyriad import AnalysisTree, forest_plot, distribution_plot
    >>> 
    >>> # Build analysis with plot-ready statistics
    >>> tree = AnalysisTree().split_by('df.Treatment').analyze_by(
    ...     effect=lambda df: np.mean(df.Outcome),
    ...     ci_width=lambda df: 1.96 * np.std(df.Outcome) / np.sqrt(len(df))
    ... )
    >>> result = tree.run(df)
    >>> 
    >>> # Create forest plot
    >>> forest_plot(result, x='effect', x_err='ci_width')
    >>> 
    >>> # Create distribution plot
    >>> distribution_plot(result, x='Outcome', type='scatter')

See also:
    - examples/04_plots.ipynb: Comprehensive plotting examples
    - tabular.py: Data preparation for plotting
"""

from .tabular import flatten, flatten_data
import pandas as pd
import numpy as np
from difflib import get_close_matches
import warnings

import matplotlib.pyplot as plt
import seaborn as sns

def forest_plot(dtree, x:str = "x", x_err:str = "err", col:str = (), type:str = "forest", jitter:bool = False, show = True):
    """Create a forest plot from a DataTree object.

    Args:
        dtree (DataTree): The DataTree object containing the analysis results.
        x (str, optional): The column name for the x-axis values. Defaults to "x".
        x_err (str, optional): The column name for the x-axis error values. Defaults to "err".
        col (str or list of str, optional): Column(s) to facet the plot by. Defaults to ().
        type (str, optional): The type of plot to create. Currently only "forest" is supported. Defaults to "forest".
        jitter (bool, optional): Whether to apply jittering to the y-axis positions to avoid overplotting. Defaults to False.
        show (bool, optional): Whether to display the plot immediately. If False, returns the figure object. Defaults to True.

    Returns:
        None: Displays the plot using matplotlib's show().

    Examples:
        >>> tree = AnalysisTree().split_by('df.Gender').analyze_by(
        ...     x=lambda df: np.mean(df.Income),
        ...     err=lambda df: np.std(df.Income) / np.sqrt(len(df))
        ... )
        >>> result = tree.run(df)
        >>> forest_plot(result)
        
        >>> # Forest plot with faceting by split
        >>> forest_plot(result, col='df.Gender', jitter=True)
    """

    res = flatten(dtree, unnest=True, by = col)

    # Preprocess to allow pivot
    res['pivot_lvl'] = res['pivot_lvl'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['pivot_split'] = res['pivot_split'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['label'] = res.apply(lambda row: "__not__analysis__" if (row["type"] != "analysis") else row["label"], axis = 1)
    res['label'] = res['label'].apply(lambda x: "Unlabelled" if len(x) == 0 else x) # 0 len label make pivot delete the corresponding lines.

    # Remove the last element from path_pivot for y_label
    res['y_label'] = res.apply(lambda row: str(row['path_pivot'][-2]) if row['type'] == "analysis" else row['lvl'] or row['split'] or "root", axis=1)

    # Remove unnecessary rows
    available_analysis = res.loc[res['type'] == "analysis", 'path_pivot'].apply(lambda x: x[:-1])
    available_analysis = available_analysis.apply(lambda x: " >> ".join(x)).unique()
    res['path_pivot'] = res['path_pivot'].apply(lambda x: " >> ".join(x))
    res = res.loc[~(res['path_pivot'].isin(available_analysis) & (res['type'] != "analysis"))]

    # Move index to column for pivot
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

    # remove rows that are not analysis from data but keep the full data frame for y_label calculation
    res_data = res.loc[res["label"] != '__not__analysis__', :].copy()

    # introducing jittering based on col
    if ((len(res_data['pivot_lvl'].unique()) > 1) & jitter):
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
    if show:
        plt.show()
    return g


def plot_1d(data, type:str = "forest", x:str = "x", x_err:str = "err", **kwargs):
    """Create a 1D plot.

    Args:
        data (pd.DataFrame): The DataFrame containing the plot data.
        type (str, optional): The type of plot to create. Currently supports "forest", "range", "bar", "point". Defaults to "forest".
        x (str, optional): The column name for the x-axis values. Defaults to "x".
        x_err (str, optional): The column name for the x-axis error values. Defaults to "err".
        **kwargs: Additional keyword arguments passed to matplotlib plotting functions.

    Returns:
        None: Adds plot elements to the current matplotlib axes.

    Examples:
        >>> data = pd.DataFrame({'x': [1.5, 2.3], 'err': [0.2, 0.3], 'y_jitter': [0, 1]})
        >>> plot_1d(data, type='forest', x='x', x_err='err')
        
        >>> # Point plot without error bars
        >>> plot_1d(data, type='point', x='x')
        
        >>> # Bar plot
        >>> plot_1d(data, type='bar', x='x')
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
    



def distribution_plot(dtree, type:str="scatter", x:str = None, col:str = (), jitter:bool = False, show = True):
    """Create a distribution plot from a DataTree object.

    Args:
        dtree (DataTree): The DataTree object containing the analysis results with raw data.
        type (str, optional): The type of plot to create. Currently supports "scatter", "boxplot". Defaults to "scatter".
        x (str, optional): The column name for the x-axis values. If None, attempts to auto-detect. Can also be a dict mapping facet labels to column names.
        col (str or list of str, optional): Column(s) to facet the plot by. Defaults to ().
        jitter (bool, optional): Whether to apply jittering to the y-axis positions to avoid overplotting. Defaults to False.
        show (bool, optional): Whether to display the plot immediately. If False, returns the figure object. Defaults to True.

    Returns:
        None: Displays the plot using matplotlib's show().

    Examples:
        >>> tree = AnalysisTree().split_by('df.Gender').analyze_by(
        ...     income_data=lambda df: df[['Income']]
        ... )
        >>> result = tree.run(df)
        >>> distribution_plot(result, x='Income', type='scatter')
        
        >>> # With faceting and jitter
        >>> distribution_plot(result, x='Income', col='df.Gender', jitter=True)
        
        >>> # Boxplot
        >>> distribution_plot(result, x='Income', type='boxplot')
    """

    res = flatten_data(dtree, unnest=False, by = col)

    # Preprocess to allow pivot
    res['pivot_lvl'] = res['pivot_lvl'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['pivot_split'] = res['pivot_split'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['label'] = res.apply(lambda row: "__not__analysis__" if (row["type"] != "analysis") else row["label"], axis = 1)
    res['label'] = res['label'].apply(lambda x: "Unlabelled" if len(x) == 0 else x) # 0 len label make pivot delete the corresponding lines.

    # Remove the last element from path_pivot for y_label
    res['y_label'] = res.apply(lambda row: str(row['path_pivot'][-2]) if row['type'] == "analysis" else row['lvl'] or row['split'] or "root", axis=1)

    # Remove unnecessary rows
    available_analysis = res.loc[res['type'] == "analysis", 'path_pivot'].apply(lambda x: x[:-1])
    available_analysis = available_analysis.apply(lambda x: " >> ".join(x)).unique()
    res['path_pivot'] = res['path_pivot'].apply(lambda x: " >> ".join(x))
    res = res.loc[~(res['path_pivot'].isin(available_analysis) & (res['type'] != "analysis"))]

    # res = res.reset_index().rename(columns={'index': '_id'})

    # Find the rank if the values in the y columns
    # - "dense" is not working because it is not respecting alphabetic order.
    # - "first" is not working because we need dense.
    rank_dict = {p: -i for i, p in enumerate(res.loc[~res['path_pivot'].duplicated(), 'path_pivot'])}
    res['y'] = res['path_pivot'].map(rank_dict)

    res['y_label'] = res.apply(lambda row: (" " * row['depth'] * 2) + row['y_label'], axis=1)

    # TODO: remove the split to the top left
    # TODO: add color map to the side of the plot if col is not None

    # remove rows that are not analysis from data but keep the data frame for y_label calculation
    res_data = res.loc[res["label"] != '__not__analysis__', :].copy()

    # introducing jittering based on colour
    if ((len(res_data['pivot_lvl'].unique()) > 1) & jitter):
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
            # find the name of the current facet
            facet_name = g.col_names[i % len(g.col_names)]

    # Set the x-axis label for each facet
    for i, ax in enumerate(g.axes.flat):
        facet_name = g.col_names[i % len(g.col_names)]
        if isinstance(x, str):
            ax.set_xlabel(x)
        elif isinstance(x, dict):
            ax.set_xlabel(x[facet_name])

    g.add_legend(title = "".join(res["pivot_split"].unique().tolist()))

    plt.subplots_adjust(wspace=0.2)
    plt.show()

def plot_distribution(data, type:str = "scatter", x:str = None, **kwargs):
    """Create a distribution plot from data with nested summary DataFrames.

    Args:
        data (pd.DataFrame): The DataFrame containing the data to plot with 'summary' column.
        type (str, optional): The type of plot to create. Currently supports "scatter", "boxplot". Defaults to "scatter".
        x (str, optional): The column name for the x-axis values. Can be a string, dict, or None for auto-detection.
        **kwargs: Additional keyword arguments passed to matplotlib plotting functions.

    Returns:
        None: Adds plot elements to the current matplotlib axes.

    Examples:
        >>> # Data with nested summary column
        >>> data = pd.DataFrame({
        ...     'summary': [pd.DataFrame({'values': [1, 2, 3]})],
        ...     'y_jitter': [0],
        ...     'label': ['Group A']
        ... })
        >>> plot_distribution(data, type='scatter', x='values')
        
        >>> # With dict mapping for different facets
        >>> plot_distribution(data, type='scatter', x={'Group A': 'values'})
    """
    y = "y_jitter"
    # The data are nested in a data frame in the "summary" column.
    x_series = data["summary"]

    if isinstance(x, str):
        assert x in x_series.iloc[0].columns, f"{x} not found in the data, available columns: {x_series.iloc[0].columns.tolist()}"
        x_series = x_series.apply(lambda row: list(row[x])).explode()
        x_label = x
    elif isinstance(x, dict):
        current_facet = data["label"].unique().tolist()[0]
        x_series = x_series.apply(lambda row: list(row[x[current_facet]])).explode()
        x_label = x[current_facet]
    elif x is None:
        # for the column with the name most similar to the current facet
        current_facet = data["label"].unique().tolist()[0]
        possible_x = x_series.iloc[0].columns.tolist()
        # find the column with the most similar name to current_facet
        close_matches = get_close_matches(current_facet, possible_x, n=1, cutoff=0.1)
        if len(close_matches) == 0:
            raise ValueError(f"Could not find a column name similar to the facet name: {current_facet}. Please provide an explicit x mapping.")
        x_col = close_matches[0]
        x_series = x_series.apply(lambda row: list(row[x_col])).explode()
        x_label = x_col

        warnings.warn(f"Warning: x parameter is None. Using column '{x_col}' for facet '{current_facet}'.")
    else:
        raise ValueError("x must be a string or a dictionary mapping facet labels to column names.")
    
    y_series = data[[y, "y_label", "pivot_lvl"]]
    merge_data = pd.merge(y_series, x_series, left_index=True, right_index=True, how='left')

    y_lab = data["y_label"].to_list()

    if type == "scatter":
        plt.scatter(
            merge_data["summary"], 
            merge_data[y],
            marker='|',
            linestyle=''
        )
        plt.xlabel(x_label)

    elif type == "boxplot":
        # Align boxplots with their corresponding numeric y values using matplotlib
        grouped_data = merge_data.groupby(y)
        box_data = [group["summary"].values for name, group in grouped_data]
        unique_y = [float(x) for x in grouped_data.groups.keys()]
        plt.boxplot(
            box_data,
            vert=False,  # Horizontal boxplots
            positions=unique_y,  # Numeric y positions
            patch_artist=True,
            widths=0.19  # Colored boxes
        )
        plt.xlabel(x_label)
        

    elif type == "violin":
        # Align violin plots with their corresponding numeric y values using matplotlib
        grouped_data = merge_data.groupby(y)
        violin_data = [group["summary"].values.tolist() for name, group in grouped_data]
        unique_y = [float(x) for x in grouped_data.groups.keys()]
        plt.violinplot(
            violin_data,
            vert=False,  # Horizontal violins
            positions=unique_y,  # Numeric y positions,
            showmedians=True
        )
        plt.xlabel(x_label)

        quantile_data = [np.percentile(x, [25, 50, 75]) for x in violin_data]
        # Overlay quantile lines
        for i, y_pos in enumerate(unique_y):
            q1, median, q3 = quantile_data[i]
            plt.plot([q1, q3], [y_pos, y_pos], color = "k", linewidth=4, alpha=0.2)  # IQR line

    else:
        raise ValueError(f"Unknown plot type: {type}")


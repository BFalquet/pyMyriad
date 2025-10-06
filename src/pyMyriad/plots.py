from .tabular import flatten
import pandas as pd
import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# import plotly.io as pio

import matplotlib.pyplot as plt
import seaborn as sns

# Set default renderer to browser for better terminal compatibility
# pio.renderers.default = 'browser'

def forest_plot(dtree, x:str = "x", x_err:str = "err", col:str = (), show = True):
    """Create a forest plot from a DataTree object.

    Args:
        dtree (DataTree): The DataTree object containing the analysis results.
        x (str, optional): The column name for the x-axis values. Defaults to "x".
        x_err (str, optional): The column name for the x-axis error values. Defaults to "err".
        col (str or list of str, optional): Column(s) to facet the plot by. Defaults to ().
        show (bool, optional): Whether to display the plot immediately. If False, returns the figure object. Defaults to True.

    Examples:

    """

    res = flatten(dtree, unnest=True, by = col)

    res['pivot_lvl'] = res['pivot_lvl'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['pivot_split'] = res['pivot_split'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['label'] = res['label'].apply(lambda x: "" if x is None else str(x))

    # Remove the last element from path_pivot for y_label
    res['y_label'] = res.apply(lambda row: str(row['path_pivot'][-2]) if row['type'] == "analysis" else row['lvl'] or row['split'] or "Overall", axis=1)

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

    # Reset index so 'index' becomes a column again
    res = res.reset_index()

    # find the rank if the values in the y columns
    # dense is not working because it is not respecting alphabetic order.
    # first is not working because we need dense.
    rank_dict = {p: -i for i, p in enumerate(res.loc[~res['path_pivot'].duplicated(), 'path_pivot'])}
    res['y'] = res['path_pivot'].map(rank_dict)

    res['y_label'] = res.apply(lambda row: (" " * row['depth'] * 2) + row['y_label'], axis=1)

    g = sns.FacetGrid(res, col="label", hue = "pivot_lvl", sharey=True)
    # g.map_dataframe(sns.scatterplot, x=x, y="y", hue="pivot_lvl")

    def errorbar_plot(data, **kwargs):
        plt.errorbar(
            data[x], 
            data["y"],
            xerr=data[x_err], 
            marker='o', 
            linestyle=''
       )

    g.map_dataframe(errorbar_plot)

    max_label_len = np.max(res['y_label'].apply(len))
    print(max_label_len)
 
    # First invert the y-axis, then set the ticks
    def set_ticks(data, **kwargs):
        ax = plt.gca()  # Gets the current axis for the facet
        ax.set_yticks(ticks=res['y'], labels=res['y_label'])  # Use 'res' not 'data'
        ax.tick_params(axis='y', which='major', labelsize='medium', pad=max_label_len * 5)
        ax.yaxis.set_tick_params(labelleft=True, labelright=False)
        for tick in ax.get_yticklabels():
            tick.set_horizontalalignment('left')

    g.map_dataframe(set_ticks)

    plt.show()




    
    # fig = px.scatter(
    #     res,
    #     x = x,
    #     error_x = x_err,
    #     y = "y",
    #     facet_col = "label",      # Creates column-wise facets
    #     color="pivot_lvl"            # Colors points by group
    # )

    # # update every facets.
    # fig.update_yaxes(
    #     title = dict(text = ""),
    #     tickvals = res['y'],
    #     ticktext = res['y_label'],
    #     autorange = "reversed",
    #     showline = True,
    #     linewidth = 1,
    #     linecolor = 'black',
    #     mirror = True,
    #     showgrid = False,
    #     automargin = True,
    #     ticklabelposition="outside left",  # ensures they’re left of the axis
    #     ticklabeloverflow="allow"          # prevents clipping
    #     # ticklabelalign="left"              # left-justify the tick labels
    # )

    # fig.update_xaxes(
    #     matches=None,
    #     showline = True,
    #     linewidth = 1,
    #     linecolor = 'black',
    #     mirror = True,
    #     showgrid = False
    # )

    # fig.for_each_annotation(lambda x: x.update(text = str(x.text.split("=")[1])))
    # fig.for_each_trace(lambda x: x.update(name = str(x.name.split("=")[0])))

    # if show:
    #     # Force browser rendering for reliable display
    #     fig.show(renderer='browser')
    #     return res
    # else:
    #     return fig
from .tabular import flatten
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Set default renderer to browser for better terminal compatibility
pio.renderers.default = 'browser'

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

    # For inline presentation
    # Remove the last element from path_pivot for y_label
    inline = True
    if (inline):
        res['y_label'] = res.apply(lambda row: str(row['path_pivot'][-2]) if row['type'] == "analysis" else row['lvl'] or row['split'] or "Overall", axis=1)

    available_analysis = res.loc[res['type'] == "analysis", 'path_pivot'].apply(lambda x: x[:-1])
    available_analysis = available_analysis.apply(lambda x: " >> ".join(x)).unique()

    res['path_pivot'] = res['path_pivot'].apply(lambda x: " >> ".join(x))
    res = res.loc[~(res['path_pivot'].isin(available_analysis) & (res['type'] != "analysis"))]
    # res['y'] = pd.Categorical(res['path_pivot'], ordered = True).codes

    res = res.reset_index().rename(columns={'index': '_id'})

    res = res.pivot(
       index = ["_id", "split", "type", "path_pivot", "pivot_lvl", "pivot_split", "label", "y_label"], # y
       columns = "statistics",
       values = "values"
    )

    # res = res.loc[(res["split"] != res["pivot_split"])]

    # Reset index so 'index' becomes a column again
    res = res.reset_index()

    # find the rank if the values in the y columns

    res['y'] = res['_id'].rank(method = 'dense')
    
    fig = px.scatter(
        res,
        x = x,
        error_x = x_err,
        y = "y",
        facet_col = "label",      # Creates column-wise facets
        color="pivot_lvl"            # Colors points by group
    )

    # update every facets.
    fig.update_yaxes(
        title = dict(text = ""),
        tickvals = res['y'],
        ticktext = res['y_label'],
        autorange = "reversed",
        showline = True,
        linewidth = 1,
        linecolor = 'black',
        mirror = True,
        showgrid = False,
        automargin = True
    )

    fig.update_xaxes(
        matches=None,
        showline = True,
        linewidth = 1,
        linecolor = 'black',
        mirror = True,
        showgrid = False
    )

    fig.for_each_annotation(lambda x: x.update(text = str(x.text.split("=")[1])))
    fig.for_each_trace(lambda x: x.update(name = str(x.name.split("=")[0])))

    if show:
        # Force browser rendering for reliable display
        fig.show(renderer='browser')
        return res
    else:
        return fig
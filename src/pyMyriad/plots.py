from .tabular import flatten
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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

    res['path_pivot'] = res['path_pivot'].apply(lambda x: " >> ".join(x))
    res['pivot_lvl'] = res['pivot_lvl'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    res['pivot_split'] = res['pivot_split'].apply(lambda x: ".none" if x is None else " >> ".join(x))
    # res['label'] = res['label'].apply(lambda x: None if x is None else "".join(x))

    res = res.pivot(
       index = ["split", "type", "path_pivot", "pivot_lvl", "pivot_split", "label"],
       columns = "statistics",
       values = "values"
    ).reset_index()

    res = res.loc[(res["split"] != res["pivot_split"]) & (res['type'] != "split")]
    res['y'] = pd.factorize(res['path_pivot'])[0]

    fig = px.scatter(
        res,
        x = x,
        error_x = x_err,
        y = "y",
        facet_col = "label",      # Creates column-wise facets
        color="pivot_lvl"            # Colors points by group
    )

    if show:
        fig.show()
    else:
        return fig
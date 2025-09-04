from .tabular import flatten
import pandas as pd
import numpy as np
import plotly.express as px 
import plotly.graph_objects as go

def forest_plot(dtree, x:str = "x", x_err:str = "err", col:str = (), show = True):

    res = flatten(dtree, unnest=True, by = col)

    res['path_pivot'] = res['path_pivot'].apply(lambda x: "".join(x))
    res['pivot_lvl'] = res['pivot_lvl'].apply(lambda x: ".none" if x is None else "".join(x))
    res['pivot_split'] = res['pivot_split'].apply(lambda x: ".none" if x is None else "".join(x))
    res['label'] = res['label'].apply(lambda x: ".none" if x is None else "".join(x))

    # print(
    #    res.loc[res[['type' 'path_pivot', 'pivot_lvl', 'label']].duplicated()]
    # )


    res = res.pivot(
       index = ["split", "type", "path_pivot", "pivot_lvl", "pivot_split", "label"],
       columns = "statistics",
       values = "values"
    ).reset_index()

    res = res.loc[(res["split"] != res["pivot_split"]) & (res['type'] != "split")]

    print(res)

    # res['y'] = pd.factorize(res['path_pivot'])[0] + (pd.factorize(res['pivot_lvl'])[0] + 1 / max(pd.factorize(res['pivot_lvl'])[0] + 1)) - np.median(pd.factorize(res['pivot_lvl'])[0] + 1)

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
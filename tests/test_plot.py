import pytest
from pyMyriad.analysis_tree import AnalysisTree, SplitNode, AnalysisNode
from pyMyriad.plots import forest_plot

import pandas as pd
import numpy as np
from importlib import import_module
from contextlib import contextmanager

@contextmanager
def with_module(module_name, module_abr):
    """Temporarily provide an environment with a specific module available."""
    try:
        # Import the requested module
        module = import_module(module_name)
        # Create environment with just this module
        environ = {module_abr: module}
        yield environ
    finally:
        pass

def test_forest_plot():
    atree = AnalysisTree().split_by("df.VAR1").split_by("df.VAR2 > 50").analyze_by(m = "np.mean(df.val)", std = "np.std(df.val)")
    df = pd.DataFrame({
        "VAR1": ["A", "A", "A", "B", "B", "B"],
        "VAR2": [10, 60, 70, 20, 80, 90],
        "val": [1, 2, 3, 4, 5, 6]
    })
    with with_module('numpy', 'np') as environ:
        dtree = atree.run(df, environ = environ)
    fig = forest_plot(dtree, x = "m", x_err  = "std", show = False)
    assert fig is not None
    assert len(fig.data) > 0

    fig = forest_plot(dtree, col = "df.VAR1", x = "m", x_err  = "std", show = False)
    assert fig is not None
    assert len(fig.data) > 0


import pandas as pd
import numpy as np
from pyMyriad.analysis_tree import AnalysisTree, SplitNode, AnalysisNode
from pyMyriad.plots import forest_plot

atree = AnalysisTree().split_by("df.VAR1").split_by("df.VAR2 > 50").analyze_by(m = "np.mean(df.val)", std = "np.std(df.val)")
df = pd.DataFrame({
    "VAR1": ["A", "A", "A", "B", "B", "B"],
    "VAR2": [10, 60, 70, 20, 80, 90],
    "val": [1, 2, 3, 4, 5, 6]
})
dtree = atree.run(df)
print(dtree)
fig = forest_plot(dtree, x = "m", x_err  = "std")

from pyMyriad.tabular import flatten
res = flatten(dtree, unnest=True)

res['path_pivot'] = res['path_pivot'].apply(lambda x: " >> ".join(x))
res['pivot_lvl'] = res['pivot_lvl'].apply(lambda x: ".none" if x is None else " >> ".join(x))
res['pivot_split'] = res['pivot_split'].apply(lambda x: ".none" if x is None else " >> ".join(x))
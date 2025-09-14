import pandas as pd
import numpy as np
from pyMyriade.analysis_tree import AnalysisTree, SplitNode, AnalysisNode
from pyMyriade.plots import forest_plot

atree = AnalysisTree().split_by("df.VAR1").split_by("df.VAR2 > 50").analyze_by(m = "np.mean(df.val)", std = "np.std(df.val)")
df = pd.DataFrame({
    "VAR1": ["A", "A", "A", "B", "B", "B"],
    "VAR2": [10, 60, 70, 20, 80, 90],
    "val": [1, 2, 3, 4, 5, 6]
})
dtree = atree.run(df, environ = None)
fig = forest_plot(dtree, x = "m", x_err  = "std", show = False)
fig.show()

fig2 = forest_plot(dtree, col = "df.VAR1", x = "m", x_err  = "std", show = False)
fig2.show()
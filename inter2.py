import pandas as pd
import numpy as np
from pyMyriad.analysis_tree import AnalysisTree, SplitNode, AnalysisNode
from pyMyriad.plots import forest_plot

# atree = AnalysisTree().split_by("df.VAR1").split_by("df.VAR2 > 50").analyze_by(m = "np.mean(df.val)", std = "np.std(df.val)")
# df = pd.DataFrame({
#     "VAR1": ["A", "A", "A", "B", "B", "B"],
#     "VAR2": [10, 60, 70, 20, 80, 90],
#     "val": [1, 2, 3, 4, 5, 6]
# })
# dtree = atree.run(df, environ = None)
# fig = forest_plot(dtree, x = "m", x_err  = "std", show = False)
# fig.show()

# fig2 = forest_plot(dtree, col = "df.VAR1", x = "m", x_err  = "std", show = False)
# fig2.show()

import plotly.express as px


df = pd.DataFrame({
  "A": np.random.normal(0, 1, 1000),
  "B": np.random.normal(0, 1, 1000)
})

df.A > 0 | df.B > 0

atree = AnalysisTree().split_by("(df.A + df.B) > 1").analyze_by(m = "np.mean(df.B)")
print(atree)
dtree = atree.run(df)
print(dtree)


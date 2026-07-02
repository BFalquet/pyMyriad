"""
pyMyriad — hierarchical analysis tree framework for stratified data analysis.

**Building an analysis (construction side)**
  AnalysisTree   Root container; start here. ``AnalysisTree().split_by(...).analyze_by(...)``
  SplitNode      Represents a data split/stratification step.
  AnalysisNode   Represents a computation step.

**Reading results (results side)**
  DataTree       Root result container returned by ``AnalysisTree.run()``.
  SplitDataNode  Results of a split operation, keyed by level.
  LvlDataNode    Results for a single level within a split.
  DataNode       Leaf node holding computed summary statistics.

**Exporting to tables**
  simple_table   Flat pandas DataFrame, one row per analysis.
  cascade_table  Hierarchical DataFrame including split and summary rows.
  gt_table       Formatted HTML table via great-tables.

**Exporting to plots**
  forest_plot        Forest plot for effect sizes with error bars.
  distribution_plot  Distribution / scatter plot of raw data.

**Formatting**
  format_statistics      Apply format strings to combine statistics in a DataTree.

**Data preparation**
  change_from_baseline   Add a per-subject change-from-baseline column to a DataFrame.

**Clinical tables**
  lab_summary_table      Canonical clinical-trial lab table (Visit x Statistic rows, Arm x Value/Change columns).

Typical workflow::

    import pandas as pd, numpy as np
    from pyMyriad import AnalysisTree, simple_table

    tree = AnalysisTree().split_by("df.Group").analyze_by(n=lambda df: len(df))
    result = tree.run(df)
    print(simple_table(result))

See ARCHITECTURE.md for a full architectural overview.
"""

__version__ = "0.1.0"


from .analysis_tree import AnalysisTree, SplitNode, AnalysisNode
from .data_tree import DataTree, SplitDataNode, LvlDataNode, DataNode
from .plots import forest_plot, distribution_plot
from .listing import gt_table, simple_table, cascade_table
from .tabular import format_statistics, change_from_baseline
from .clinical import lab_summary_table

__all__ = [
    "AnalysisTree",
    "SplitNode",
    "AnalysisNode",
    "DataTree",
    "SplitDataNode",
    "LvlDataNode",
    "DataNode",
    "forest_plot",
    "distribution_plot",
    "gt_table",
    "simple_table",
    "cascade_table",
    "format_statistics",
    "change_from_baseline",
    "lab_summary_table",
]

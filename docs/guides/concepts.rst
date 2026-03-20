Core Concepts
=============

Understanding pyMyriad's Architecture
--------------------------------------

pyMyriad is built around two main tree structures:

**AnalysisTree** - The Blueprint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An AnalysisTree defines *how* analysis is performed. It's a hierarchical structure that specifies:

* **Split Node**: How to divide the data (like stratification)
* **Analysis Node**: What computations to perform on each group

.. code-block:: text
    Analysis Tree
    └- Split Node gender: [df.Gender]
        └- Analysis Node: wage analysis
            mean_income: mean_income=lambda df: np.mean(df.Income),
            count: count=lambda df: len(df)


**DataTree** - The Results
~~~~~~~~~~~~~~~~~~~~~~~~~~

When you run an AnalysisTree on data, you get a DataTree containing:

* **SplitDataNode**: Results organized by split groups
* **LvlDataNode**: Results for each level of a split
* **DataNode**: Leaf nodes with actual computed values

.. code-block:: text

   Data Tree
   Split: df.Gender # SplitDataNode
   └- F # LvlDataNode
     analysis: wage analysis # DataNode 
       └- mean_income: 75000.0
       └- count: 3
   └- M # LvlDataNode
     analysis: wage analysis # DataNode
       └- mean_income: 55000.0
       └- count: 3


Tree Construction Methods
--------------------------

Analysis trees are constructed gradually by adding split and analysis nodes to a root. 

AnalysisTree() 

initializes the tree.

.. code -block:: python

   tree = AnalysisTree()  # Start with an empty tree


split_by()
~~~~~~~~~~

Adds splits at the leaf nodes of all branches. Using the `df` variable as the DataFrame, one can specify either
* a column to split by (e.g. `'df.Gender'`) which creates one branch per unique value in that column of the analysis dataset.
* or custom split conditions (e.g. `'df.Country != "UK"'`) which creates two branches based on the condition being true or false.
* or specify what should be in each group using keyword arguments (e.g. `Low_mid_income='df.Income < 70000'`, `High_mid_income='df.Income >= 50000'`). With this last approach, once can create overalapping or non-exhaustive groups.

Use the `label` argument to specify a custom label for the split node. By default, the split expression is used as the label.

.. code-block:: python

   tree = AnalysisTree() 
   tree.split_by('df.Gender', label = "gender")
   tree.split_by('df.Country != "UK"', label = "UK vs non-UK")
   tree.split_by(Low_income='df.Income < 50000', High_income='df.Income >= 50000', label ="Income level")

analyze_by()
~~~~~~~~~~~~

Adds analysis nodes at the leaf nodes:

.. code-block:: python

   tree.analyze_by(
       mean=lambda df: np.mean(df.Income),
       std=lambda df: np.std(df.Income),
       label="wage analysis"
   )

Split and analyze at specific locations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, split_by() and analyze_by() add nodes at the leaf nodes of all branches. To add nodes at specific locations, use `split_at_by()` and `analyze_at_by()`, which take a `path` argument specifying where to add the nodes. 
The `path` is a list of the labels of the split nodes that define the branch where the new nodes should be added. 
For example, `path=['df.Gender']` would add nodes to `splitNode` named `df.Gender`. Use `"*"` as a wildcard to mean "any label".

.. code-block:: python

   tree = AnalysisTree()
   tree.split_by('df.Gender', label="Gender")
   tree.split_by('df.Country', label="US vs non-US")
   tree.split_at_by(["Gender"], "df.Income") # Add split by income downstream of the gender split.
   tree.split_at_by(["*", "US vs non-US"], "df.Age") # Add split by age downstream of the US vs non-US split.
   tree.split_at_by([], "df.Education") # Add split by education at the root of the tree (i.e. before any other splits)

Use `analyze_at_by()` in the same way to add analysis nodes at specific locations in the tree.

.. code-block:: python

   tree = AnalysisTree()
   tree.split_by('df.Gender', label="Gender")
   tree.split_by('df.Country', label="US vs non-US")
   tree.analyze_at_by(["Gender"], n=lambda df: len(df), label="Count") # Add summary by count downstream of the gender split.
   tree.analyze_at_by(["*", "US vs non-US"], m=lambda df: np  .mean(df.Income), label="Mean Income") # Add summary by mean income downstream of the US vs non-US split.

Termination Signals
~~~~~~~~~~~~~~~~~~~

The addition of an analysis node blocks the addition of further splits downstream of that node. 
To allow further splits, set `termination=False` when adding the analysis node or use `summarize_by()` or `summarize_at_by()` instead of `analyze_by()` or `analyze_at_by()`, which have `termination=False` by default.

.. code-block:: python

   # Doesn't stop further splits
   tree.summarize_by(count=lambda df: len(df), termination=False)
   
   # Stops further splits (default behavior)
   tree.analyze_by(mean=lambda df: np.mean(df.Income), termination=True)

Cross-Group Analysis
--------------------

To perform analyses that compare groups (e.g. treatment vs control), use `cross_analyze_by()`, 
which takes the same arguments as `analyze_by()` but also requires a `ref_lvl` argument specifying the reference group for comparison.


.. code-block:: python

   df = pd.DataFrame({
        'Treatment': ['Placebo', 'Placebo', 'Drug', 'Drug'],
        'Outcome': [1, 2, 3, 4],
        'Baseline': [0.5, 1.5, 2.5, 3.5]
   })
   tree = AnalysisTree()
   tree.split_by('df.Treatment')
   tree.cross_analyze_by(
       diff=lambda df, ref_df: np.mean(df.Outcome) - np.mean(ref_df.Outcome),
       ref_lvl='Placebo'  # Compare everything to Placebo group
   )

   tree.run(df)

In cross-analysis expressions, ``df`` is the current group and ``ref_df`` is the reference group.
Note that cross_analyze_by() creates new combination levels during the analysis (here "Drug_vs_Placebo") that are not present in the original data.

Expression Evaluation
----------------------

pyMyriad supports two ways to specify analyses:

String Expressions
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   tree.analyze_by(mean="np.mean(df.Income)")

The DataFrame is available as ``df`` in the expression. NumPy and Pandas are auto-injected as ``np`` and ``pd``.

Lambda Functions
~~~~~~~~~~~~~~~~

.. code-block:: python

   tree.analyze_by(mean=lambda df: np.mean(df.Income))

Lambda functions are more explicit and avoid import warnings.

Environment Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Set a default environment to avoid repeated configuration:

.. code-block:: python

   import numpy as np
   import pandas as pd
   
   AnalysisTree.set_default_environ({'np': np, 'pd': pd})



Data Export and Visualization
------------------------------

Once you have a DataTree, export it:

.. code-block:: python

   from pyMyriad import simple_table, forest_plot
   from pyMyriad.tabular import tabulate
   
   # To pandas DataFrame
   table = simple_table(result)
   
   # With pivoting
   table = simple_table(result, by='df.Gender', pivot_statistics=True)
   
   # To visualization
   fig = forest_plot(result)


See Also
--------

* :doc:`workflows` for complete examples
* :doc:`../api/analysis_tree` for detailed API reference
* :doc:`../examples/index` for Jupyter notebook tutorials

.. pyMyriad documentation master file

Welcome to pyMyriad's documentation!
=====================================

**pyMyriad** is a Python library for hierarchical data analysis trees, enabling flexible and reproducible analytical workflows.

Features
--------

* **Analysis Trees**: Define complex hierarchical analyses with splits and aggregations
* **Data Trees**: Execute analysis trees to generate structured results
* **Flexible Output**: Export to tables, plots, and formatted reports
* **Expression Evaluation**: Use string expressions or lambda functions for analysis logic
* **Visualization**: Built-in support for forest plots and distribution plots

Quick Start
-----------

.. code-block:: python

   import pandas as pd
   import numpy as np
   from pyMyriad import AnalysisTree
   
   # Create a simple dataset
   df = pd.DataFrame({
       'Gender': ['M', 'M', 'F', 'F'],
       'Income': [50000, 60000, 70000, 80000]
   })
   
   # Build an analysis tree
   tree = AnalysisTree().split_by('df.Gender').analyze_by(
       mean=lambda df: np.mean(df.Income),
       count=lambda df: len(df)
   )
   
   # Run the analysis
   result = tree.run(df)
   print(result)

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   
   guides/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   
   api/index

.. toctree::
   :maxdepth: 2
   :caption: Examples
   
   examples/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Quick Start Guide
=================

This guide will help you get started with pyMyriad quickly.

Installation
------------

Install pyMyriad using pip or uv:

.. code-block:: bash

   pip install pymyriad
   
   # Or with uv
   uv pip install pymyriad

Basic Example
-------------

Here's a simple example to get you started:

.. code-block:: python

   import pandas as pd
   import numpy as np
   from pyMyriad import AnalysisTree
   
   # Create a dataset
   df = pd.DataFrame({
       'Gender': ['M', 'M', 'F', 'F', 'M', 'F'],
       'Country': ['US', 'UK', 'US', 'UK', 'US', 'UK'],
       'Income': [50000, 50000, 70000, 80000, 50000, 75000]
   })
   
   # Build an analysis tree
   tree = AnalysisTree()
   tree = tree.split_by('df.Gender', label = "gender")  # Split by gender
   tree = tree.analyze_by(
       mean_income=lambda df: np.mean(df.Income),
       count=lambda df: len(df),
       label = "wage analysis"
   )
   
   # Run the analysis
   result = tree.run(df)
   print(result)

.. code-block:: text

    Data Tree
    Split: gender
        └- F
            analysis: wage analysis
            └- mean_income: 75000.0
            └- count: 3
        └- M
            analysis: wage analysis
            └- mean_income: 50000.0
            └- count: 3


Understanding the Workflow
---------------------------

The typical pyMyriad workflow consists of three steps:

1. **Define** - Create an AnalysisTree with splits and analyses
2. **Execute** - Run the tree on your data to get a DataTree
3. **Export** - Convert results to tables or visualizations

Next Steps
----------

* Learn about :doc:`concepts` to understand the architecture
* Explore :doc:`workflows` for common patterns
* Check the :doc:`../api/index` for detailed API documentation

Common Workflows
================

This guide demonstrates common analysis patterns with pyMyriad.

Stratified Analysis
-------------------

Analyze data broken down by multiple factors:

.. code-block:: python

   import pandas as pd
   import numpy as np
   from pyMyriad import AnalysisTree, simple_table
   
   df = pd.DataFrame({
       'Gender': ['M', 'M', 'F', 'F', 'M', 'F'] * 10,
       'Country': ['US', 'UK', 'US', 'UK', 'US', 'UK'] * 10,
       'Age': np.random.randint(20, 70, 60),
       'Income': np.random.randint(30000, 100000, 60)
   })
   
   # Two-level stratification
   tree = (AnalysisTree()
       .split_by('df.Gender')
       .split_by('df.Country')
       .analyze_by(
           n=lambda df: len(df),
           mean_age=lambda df: np.mean(df.Age),
           mean_income=lambda df: np.mean(df.Income)
       ))
   
   result = tree.run(df)
   table = simple_table(result)

Treatment Effect Analysis
-------------------------

Compare outcomes between treatment groups:

.. code-block:: python

   df = pd.DataFrame({
       'Treatment': ['Drug', 'Placebo'] * 50,
       'Outcome': np.random.normal(10, 2, 100),
       'Baseline': np.random.normal(8, 2, 100)
   })
   
   # Analyze by treatment with cross-group comparison
   tree = (AnalysisTree()
       .split_by('df.Treatment')
       .analyze_by(
           n=lambda df: len(df),
           mean_outcome=lambda df: np.mean(df.Outcome),
           mean_baseline=lambda df: np.mean(df.Baseline)
       )
       .cross_analyze_by(
           effect=lambda df, ref_df: np.mean(df.Outcome) - np.mean(ref_df.Outcome),
           ref_lvl='Placebo'
       ))
   
   result = tree.run(df)

Conditional Analysis
--------------------

Apply different analyses to different branches:

.. code-block:: python

   # Base tree
   tree = AnalysisTree().split_by('df.Gender')
   
   # Different analyses for different paths
   tree = tree.analyze_at_by(
       path=['M'],
       male_specific=lambda df: np.mean(df.Testosterone)
   )
   
   tree = tree.analyze_at_by(
       path=['F'],
       female_specific=lambda df: np.mean(df.Estrogen)
   )
   
   # Common analysis for all
   tree = tree.analyze_by(
       common=lambda df: len(df)
   )

Hierarchical Summarization
--------------------------

Add summary statistics at multiple levels:

.. code-block:: python

   tree = (AnalysisTree()
       .split_by('df.Region')
       .summarize_by(  # Region-level summary
           region_total=lambda df: len(df),
           termination=False
       )
       .split_by('df.Country')
       .summarize_by(  # Country-level summary
           country_total=lambda df: len(df),
           termination=False
       )
       .split_by('df.City')
       .analyze_by(  # City-level analysis
           city_total=lambda df: len(df),
           avg_population=lambda df: np.mean(df.Population)
       ))

Custom Formatting
-----------------

Format statistics with custom templates:

.. code-block:: python

   from pyMyriad.tabular import format_statistics
   
   result = tree.run(df)
   
   # Apply formatting
   formatted = format_statistics(
       result,
       remove_original=True,
       Mean = "{mean:.2f} 
       SD = "{sd:.2f}", 
       N="{n}"
   )
   
   table = simple_table(formatted)

Pivot Tables
------------

Create pivot tables with multiple dimensions:

.. code-block:: python

   # Pivot by gender
   table = simple_table(result, by='df.Gender')
   
   # Pivot statistics as columns
   table = simple_table(result, pivot_statistics=True)
   
   # Both pivots combined
   table = simple_table(result, by='df.Gender', pivot_statistics=True)

Visualization
-------------

Create publication-ready plots:

.. code-block:: python

   from pyMyriad import forest_plot, distribution_plot
   
   # Forest plot for effect sizes
   fig = forest_plot(result)
   fig.show()
   
   # Distribution plot
   fig = distribution_plot(result, variable='Income')
   fig.show()

Working with Great Tables
-------------------------

Generate formatted HTML tables:

.. code-block:: python

   from pyMyriad import gt_table
   
   # Create a great-tables formatted table
   table = gt_table(result, title="Analysis Results")
   table.save('output.html')

See Also
--------

* :doc:`concepts` for understanding the architecture
* :doc:`../examples/index` for complete notebook examples
* :doc:`../api/index` for detailed API documentation

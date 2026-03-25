Agent & System Interoperability
================================

pyMyriad analysis trees can be serialized to and from JSON, making it easy to
persist analysis plans, share them between services, or exchange them with
AI agents that need to understand, generate, or modify an analysis workflow.

Overview
--------

An :class:`~pyMyriad.analysis_tree.AnalysisTree` carries the full description of
*how* data should be analyzed — which variables to split on, how groups should be
named, what statistics to compute, and any cross-group comparisons.  Saving this
plan as JSON lets you:

* **Persist** an analysis plan alongside its results.
* **Inspect** the plan in a human-readable format.
* **Share** analysis plans across systems or languages without pickle.
* **Generate** analysis plans with an AI agent and load them into pyMyriad.
* **Transfer** plans between Python environments.

The four key methods are:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Description
   * - :meth:`~pyMyriad.analysis_tree.AnalysisTree.to_dict`
     - Serialize the tree to a plain Python ``dict``
   * - :meth:`~pyMyriad.analysis_tree.AnalysisTree.to_json`
     - Serialize to a JSON string (optionally write to a file)
   * - :meth:`~pyMyriad.analysis_tree.AnalysisTree.from_dict`
     - Reconstruct a tree from a ``dict``
   * - :meth:`~pyMyriad.analysis_tree.AnalysisTree.from_json`
     - Reconstruct a tree from a JSON string or file path


Serializing a Tree
------------------

Call :meth:`~pyMyriad.analysis_tree.AnalysisTree.to_json` on any tree:

.. code-block:: python

   import numpy as np
   import pandas as pd
   from pyMyriad import AnalysisTree

   tree = (AnalysisTree()
       .split_by("df.Gender", label="Gender")
       .split_by("df.Country", label="Country")
       .analyze_by(
           n=lambda df: len(df),
           mean_income=lambda df: np.mean(df.Income),
           label="stats",
       ))

   # Serialize to a JSON string
   json_str = tree.to_json()
   print(json_str)

The output is fully human-readable:

.. code-block:: json

   {
     "type": "AnalysisTree",
     "denom": null,
     "nodes": [
       {
         "type": "SplitNode",
         "label": "Gender",
         "drop_empty": false,
         "expr": "df.Gender",
         "nodes": [
           {
             "type": "SplitNode",
             "label": "Country",
             "drop_empty": false,
             "expr": "df.Country",
             "nodes": [
               {
                 "type": "AnalysisNode",
                 "label": "stats",
                 "termination": true,
                 "analysis": {
                   "n": "len(df)",
                   "mean_income": "np.mean(df.Income)"
                 }
               }
             ]
           }
         ]
       }
     ]
   }

Writing directly to a file
~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass a file path to write the JSON at the same time:

.. code-block:: python

   tree.to_json("analysis_plan.json")

The method always returns the JSON string regardless.


Deserializing a Tree
--------------------

From a JSON string
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   loaded_tree = AnalysisTree.from_json(json_str)

From a file
~~~~~~~~~~~

Pass the file path directly — :meth:`~pyMyriad.analysis_tree.AnalysisTree.from_json`
auto-detects whether the argument is an existing file path or a raw JSON string:

.. code-block:: python

   loaded_tree = AnalysisTree.from_json("analysis_plan.json")

Running the reconstructed tree
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After deserialization all analysis expressions are stored as plain strings.
Running the tree requires that the names referenced in those expressions (e.g.
``np``, ``pd``) are available at evaluation time.  Pass them via ``environ`` or
configure them once with :meth:`~pyMyriad.analysis_tree.AnalysisTree.set_default_environ`:

.. code-block:: python

   import numpy as np
   import pandas as pd

   # Option 1 — explicit environ on each run
   result = loaded_tree.run(df, environ={"np": np, "pd": pd})

   # Option 2 — configure once for all trees
   AnalysisTree.set_default_environ({"np": np, "pd": pd})
   result = loaded_tree.run(df)


Lambda Handling
---------------

Lambda functions cannot be stored as-is in JSON.  When a lambda is encountered
during serialization, pyMyriad extracts its **body expression** using Python's
standard ``ast`` and ``inspect`` modules:

.. code-block:: python

   # Original tree — uses lambda
   tree = AnalysisTree().analyze_by(mean=lambda df: np.mean(df.Income))

   # After serialization the lambda body becomes a plain string:
   # "analysis": { "mean": "np.mean(df.Income)" }

   # The deserialized tree is functionally equivalent:
   loaded = AnalysisTree.from_json(tree.to_json())
   result = loaded.run(df, environ={"np": np})

.. note::

   Only **lambda** functions are serializable this way.  Regular
   ``def`` functions cannot be reduced to a single expression.  If a
   non-lambda callable is encountered, a ``UserWarning`` is issued and
   the expression is stored as ``"<unserializable>"``.  Replace such
   callables with equivalent lambdas or string expressions before
   serializing.


JSON Schema Reference
---------------------

All serialized trees share the same recursive structure.

**AnalysisTree** (root)

.. code-block:: json

   {
     "type": "AnalysisTree",
     "denom": null,
     "nodes": [ ... ]
   }

``denom`` is ``null`` or a column name / list of column names used for
denominator counting (see :class:`~pyMyriad.analysis_tree.AnalysisTree`).

**SplitNode — single expression**

.. code-block:: json

   {
     "type": "SplitNode",
     "label": "Gender",
     "drop_empty": false,
     "expr": "df.Gender",
     "nodes": [ ... ]
   }

**SplitNode — named groups**

.. code-block:: json

   {
     "type": "SplitNode",
     "label": "income_groups",
     "drop_empty": false,
     "kwexpr": {
       "high": "df.Income > 70000",
       "low": "df.Income <= 70000"
     },
     "nodes": [ ... ]
   }

**AnalysisNode**

.. code-block:: json

   {
     "type": "AnalysisNode",
     "label": "stats",
     "termination": true,
     "analysis": {
       "n": "len(df)",
       "mean": "np.mean(df.Income)"
     }
   }

**CrossAnalysisNode**

.. code-block:: json

   {
     "type": "CrossAnalysisNode",
     "label": "diff",
     "termination": true,
     "ref_lvl": "F",
     "analysis": {
       "delta": "np.mean(df.Income) - np.mean(ref_df.Income)"
     }
   }

``ref_lvl`` is the name of the reference level; an empty string means every
pair of levels is compared (see
:meth:`~pyMyriad.analysis_tree.AnalysisTree.cross_analyze_by`).


End-to-End Agent Workflow
--------------------------

A typical agent interaction looks like this:

1. **Agent receives the JSON** describing the desired analysis plan.
2. **Agent optionally modifies** the JSON to adjust split variables or add
   analyses.
3. **pyMyriad loads the plan** and runs it against the actual data.

.. code-block:: python

   import json
   import numpy as np
   import pandas as pd
   from pyMyriad import AnalysisTree

   # --- Step 1: agent produces (or modifies) the JSON plan ---
   plan_json = json.dumps({
       "type": "AnalysisTree",
       "denom": None,
       "nodes": [
           {
               "type": "SplitNode",
               "label": "Treatment",
               "drop_empty": False,
               "expr": "df.Treatment",
               "nodes": [
                   {
                       "type": "AnalysisNode",
                       "label": "outcomes",
                       "termination": True,
                       "analysis": {
                           "n": "len(df)",
                           "mean_outcome": "np.mean(df.Outcome)",
                       }
                   },
                   {
                       "type": "CrossAnalysisNode",
                       "label": "effect",
                       "termination": True,
                       "ref_lvl": "Placebo",
                       "analysis": {
                           "delta": "np.mean(df.Outcome) - np.mean(ref_df.Outcome)"
                       }
                   }
               ]
           }
       ]
   })

   # --- Step 2: load and run ---
   AnalysisTree.set_default_environ({"np": np, "pd": pd})
   tree = AnalysisTree.from_json(plan_json)

   df = pd.DataFrame({
       "Treatment": ["Drug", "Placebo"] * 50,
       "Outcome": [10.5, 8.2] * 50,
   })
   result = tree.run(df)
   print(result)


Exporting Results to JSON
--------------------------

In addition to serializing the *analysis plan*, you can serialize the
*results* — the :class:`~pyMyriad.data_tree.DataTree` produced by
:meth:`~pyMyriad.analysis_tree.AnalysisTree.run` — so that computed
statistics can be shared with LLM agents or other downstream tools.

Why export results?
~~~~~~~~~~~~~~~~~~~

An LLM agent working with your analysis may need to:

* **Interpret** computed statistics in natural language.
* **Compare** results across runs or datasets.
* **Route** downstream actions based on specific values (e.g. flag anomalies).
* **Store** results alongside the plan for reproducibility.

Basic usage
~~~~~~~~~~~

Call :meth:`~pyMyriad.data_tree.DataTree.to_json` on the result returned by
:meth:`~pyMyriad.analysis_tree.AnalysisTree.run`:

.. code-block:: python

   import numpy as np
   import pandas as pd
   from pyMyriad import AnalysisTree

   df = pd.DataFrame({
       "Gender": ["M", "F", "M", "F", "M", "F"],
       "Income": [55000, 72000, 48000, 81000, 60000, 67000],
   })

   tree = (AnalysisTree()
       .split_by("df.Gender", label="Gender")
       .analyze_by(
           n=lambda df: len(df),
           mean_income=lambda df: np.mean(df.Income),
           label="stats",
       ))

   result = tree.run(df, environ={"np": np})
   json_str = result.to_json()
   print(json_str)

The output is a compact, hierarchical JSON document:

.. code-block:: json

   {
     "type": "DataTree",
     "_N": null,
     "children": {
       "Gender": {
         "type": "SplitDataNode",
         "split_var": "df.Gender",
         "label": "Gender",
         "children": {
           "F": {
             "type": "LvlDataNode",
             "split_lvl": "F",
             "_N": null,
             "children": {
               "stats": {
                 "type": "DataNode",
                 "label": "stats",
                 "_N": null,
                 "summary": {
                   "n": 3,
                   "mean_income": 73333.333
                 }
               }
             }
           },
           "M": {
             "type": "LvlDataNode",
             "split_lvl": "M",
             "_N": null,
             "children": {
               "stats": {
                 "type": "DataNode",
                 "label": "stats",
                 "_N": null,
                 "summary": {
                   "n": 3,
                   "mean_income": 54333.333
                 }
               }
             }
           }
         }
       }
     }
   }

Writing directly to a file
~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass a file path to write the results at the same time:

.. code-block:: python

   result.to_json("analysis_results.json")

The method always returns the JSON string regardless.


JSON structure reference
~~~~~~~~~~~~~~~~~~~~~~~~

The result JSON mirrors the four tree node types.

**DataTree** (root)

.. code-block:: json

   {
     "type": "DataTree",
     "_N": null,
     "children": { ... }
   }

``_N`` is ``null`` unless a denominator was set on the
:class:`~pyMyriad.analysis_tree.AnalysisTree` (see
:meth:`~pyMyriad.analysis_tree.AnalysisTree.__init__`).

**SplitDataNode**

.. code-block:: json

   {
     "type": "SplitDataNode",
     "split_var": "df.Gender",
     "label": "Gender",
     "children": { ... }
   }

**LvlDataNode**

.. code-block:: json

   {
     "type": "LvlDataNode",
     "split_lvl": "F",
     "_N": null,
     "children": { ... }
   }

**DataNode** (leaf)

.. code-block:: json

   {
     "type": "DataNode",
     "label": "stats",
     "_N": null,
     "summary": {
       "n": 3,
       "mean_income": 73333.333
     }
   }

Only the ``summary`` dictionary is exported. The raw ``data`` attribute
(the underlying :class:`pandas.DataFrame`) is intentionally excluded to keep
output compact and suitable for LLM context windows.


Special value handling
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Input value
     - JSON output
   * - ``float("nan")``, ``numpy.nan``
     - ``"NaN"`` (string)
   * - ``float("inf")``, ``numpy.inf``
     - ``"Infinity"`` (string)
   * - ``float("-inf")``, ``-numpy.inf``
     - ``"-Infinity"`` (string)
   * - ``numpy.int64``, ``numpy.float64``
     - Native Python ``int`` / ``float``
   * - Other non-serializable objects
     - ``str(val)`` fallback

This ensures the JSON is always valid and that LLM agents receive a
human-readable representation of edge-case values.


Combined plan + results workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Share both the analysis *plan* and *results* with an LLM agent in a single
call:

.. code-block:: python

   import json
   import numpy as np
   import pandas as pd
   from pyMyriad import AnalysisTree

   df = pd.DataFrame({
       "Treatment": ["Drug", "Placebo"] * 50,
       "Outcome": [10.5, 8.2] * 50,
   })

   tree = (AnalysisTree()
       .split_by("df.Treatment", label="Treatment")
       .analyze_by(
           n=lambda df: len(df),
           mean_outcome=lambda df: np.mean(df.Outcome),
           label="outcomes",
       ))

   AnalysisTree.set_default_environ({"np": np})
   result = tree.run(df)

   payload = {
       "plan": json.loads(tree.to_json()),
       "results": json.loads(result.to_json()),
   }
   # payload can now be passed directly to an LLM agent


See Also
--------

* :doc:`concepts` — understanding the tree structure
* :doc:`workflows` — common analysis patterns
* :class:`~pyMyriad.analysis_tree.AnalysisTree` — full API reference
* :class:`~pyMyriad.data_tree.DataTree` — result tree API reference


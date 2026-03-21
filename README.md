# pyMyriad

A Python library for hierarchical data analysis trees, enabling flexible and reproducible analytical workflows.

## Features

- **Analysis Trees**: Define complex hierarchical analyses with splits and aggregations
- **Data Trees**: Execute analysis trees to generate structured results
- **Flexible Output**: Export to tables, plots, and formatted reports
- **Expression Evaluation**: Use string expressions or lambda functions for analysis logic
- **Visualization**: Built-in support for forest plots and distribution plots
- **Great Tables Integration**: Generate publication-ready HTML tables

## Installation

```bash
pip install -e .
```

For development with documentation tools:

```bash
pip install -e ".[docs]"
```

## Quick Start

```python
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
```

## Architecture Overview

pyMyriad uses a two-phase pattern: **construction** and **execution**.

1. **Construction Phase**: Build an analysis specification using `AnalysisTree`, `SplitNode`, and `AnalysisNode`
2. **Execution Phase**: Run the tree on data with `.run()` to get a `DataTree` with results

```
Construction → Execution → Results

AnalysisTree  .run(df)→  DataTree
├─ SplitNode          →  ├─ SplitDataNode
│  └─ AnalysisNode    →  │  └─ DataNode
└─ AnalysisNode       →  └─ DataNode
```

**Key Modules**:
- [`analysis_tree.py`](src/pyMyriad/analysis_tree.py) - Tree construction (AnalysisTree, SplitNode, AnalysisNode)
- [`data_tree.py`](src/pyMyriad/data_tree.py) - Result structures (DataTree, SplitDataNode, DataNode)
- [`utils.py`](src/pyMyriad/utils.py) - Expression evaluation (scope_eval, scope_cross_eval)
- [`listing.py`](src/pyMyriad/listing.py) - Table generation (simple_table, gt_table)
- [`plots.py`](src/pyMyriad/plots.py) - Visualization (forest_plot, distribution_plot)
- [`tabular.py`](src/pyMyriad/tabular.py) - Data flattening and formatting

📖 **For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md)**

## Project Structure

```
pyMyriade/
├── src/pyMyriad/          # Main package source code
│   ├── __init__.py        # Package exports
│   ├── analysis_tree.py   # Tree construction logic
│   ├── data_tree.py       # Result data structures
│   ├── utils.py           # Expression evaluation utilities
│   ├── listing.py         # Table generation functions
│   ├── plots.py           # Plotting functions
│   ├── tabular.py         # Data flattening and formatting
│   └── cli.py             # Command-line interface
├── tests/                 # Test suite
│   ├── test_analysis_tree.py
│   ├── test_run.py
│   ├── test_tree_construction.py
│   └── ...
├── docs/                  # Sphinx documentation
│   ├── guides/            # User guides and tutorials
│   ├── api/               # API reference
│   └── examples/          # Example notebooks
├── examples/
│   └── notebooks/         # Jupyter notebook tutorials
├── ARCHITECTURE.md        # Architecture documentation for AI agents
├── README.md              # This file
└── pyproject.toml         # Project configuration
```

## Documentation

Full documentation is available in the `docs/` directory. To build the documentation locally:

```bash
cd docs
make html
```

The generated HTML documentation will be in `docs/_build/html/index.html`.

### Documentation Structure

- **User Guides**: Learn core concepts, workflows, and best practices
- **API Reference**: Complete API documentation with examples
- **Jupyter Notebooks**: Interactive tutorials in `examples/notebooks/`

## Development

Run tests:

```bash
pytest
```

## License

See LICENSE file for details.

---

### TODO

- tree contstruction
  - split_at => done
  - split_root => done
  - summarize (analyze without termination) => done

- Tabular
    - column pivot
    - in-line printing
    - transformation to gt

- plots
    - introduce legend for the colors
    - change type to a dictionary to allow the display of different plot type in the same plot.
    - more control on the colors (e.g a `by` argument mutually exclusive with a `col` argument)

- documentation
  - provide a few example 
  -  


print method
  - clean up a bit to make the structure more appearant



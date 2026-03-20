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



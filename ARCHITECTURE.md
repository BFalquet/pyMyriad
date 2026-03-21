# pyMyriad Architecture

> **For AI Agents**: This document provides a comprehensive overview of pyMyriad's architecture, design patterns, and key concepts. Read this first to understand the codebase structure.

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Class Hierarchy](#class-hierarchy)
- [The Two-Phase Pattern](#the-two-phase-pattern)
- [Expression Evaluation System](#expression-evaluation-system)
- [Main Entry Points](#main-entry-points)
- [Module Guide](#module-guide)
- [Testing Patterns](#testing-patterns)

## Overview

**pyMyriad** is a hierarchical analysis tree framework for stratified data analysis in Python. It enables defining complex analytical workflows as tree structures that can be executed on pandas DataFrames.

**Key Design Philosophy**: Separate analysis definition (construction) from execution (runtime). Analysis specifications are pure data structures that can be inspected, modified, and executed multiple times on different datasets.

## Core Concepts

### Simple vs Complex Trees

**Simple Trees** - Single analysis, no splits
```python
# Direct execution on entire dataset
tree = AnalysisTree().analyze_by(mean="np.mean(df.A)")
result = tree.run(df)  # -> Single DataNode with summary statistics
```

**Complex Trees** - Nested splits with stratified analysis
```python
# Multi-level grouping and analysis
tree = (AnalysisTree()
    .split_by('df.Gender')      # Stratify by gender
    .split_by('df.Country')     # Then by country
    .analyze_by(                # Compute statistics
        mean=lambda df: np.mean(df.Income),
        count=lambda df: len(df)
    ))
result = tree.run(df)  # -> Nested SplitDataNode/DataNode structure
```

### The Two Worlds: Construction vs Results

```
CONSTRUCTION SIDE                    RESULTS SIDE
(What to do)                        (What was computed)

AnalysisTree (list)        .run()   DataTree (dict)
  ├─ SplitNode (list)      ────>      ├─ SplitDataNode (dict)
  │   ├─ AnalysisNode               │   ├─ LvlDataNode (dict)
  │   └─ SplitNode                    │   │   └─ DataNode
  └─ AnalysisNode                     └─ DataNode
```

## Class Hierarchy

### Construction Classes (analysis_tree.py)

**AnalysisTree** (subclass of `list`)
- Root container for analysis specifications
- Contains SplitNode and AnalysisNode instances
- Key attributes:
  - `id`: Column name for counting unique entities
- Main methods:
  - `split_by()`: Add splits at leaf nodes
  - `analyze_by()`: Add analysis at leaf nodes
  - `split_at_by()`, `split_at_root_by()`: Add splits at specific locations
  - `analyze_at_by()`: Add analysis at specific location
  - `summarize_by()`: Add intermediate statistics (non-terminating)
  - `cross_analyze_by()`: Add cross-level comparisons
  - `run()`: Execute the tree on data

**SplitNode** (subclass of `list`)
- Represents data splitting/stratification logic
- Contains child nodes (SplitNode, AnalysisNode, CrossAnalysisNode)
- Key attributes:
  - `expr`: Single boolean expression or column name
  - `kwexpr`: Dictionary of named group expressions (for custom groups)
  - `label`: Human-readable label for the split

**AnalysisNode**
- Defines computations to perform
- Key attributes:
  - `analysis`: Dict of {name: expression/callable}
  - `termination`: Boolean flag (if True, prevents further splits)

**CrossAnalysisNode**
- Compares across split levels
- Key attributes:
  - `ref_lvl`: Reference level identifier for comparison
  - Provides both `df` (current) and `ref_df` (reference) to expressions

### Result Classes (data_tree.py)

**DataTree** (subclass of `dict`)
- Root result container
- Keys are split/analysis labels
- Values are SplitDataNode or DataNode instances
- Special attributes:
  - `_N`: Count of entities in the dataset

**SplitDataNode** (subclass of `dict`)
- Results of a split operation
- Each key is a level identifier, value is LvlDataNode
- Key attributes:
  - `split_var`: The splitting variable name

**LvlDataNode** (subclass of `dict`)
- A specific level within a split
- Contains DataNode or nested SplitDataNode instances
- Key attributes:
  - `split_lvl`: The level identifier (e.g., "Male", "Female")

**DataNode**
- Leaf node with actual computed results
- Key attributes:
  - `summary`: Dict of computed statistics
  - `data`: Original DataFrame (if retained)
  - `label`: Node identifier
  - `depth`: Tree depth
  - `_N`: Entity count

## The Two-Phase Pattern

### Phase 1: Construction

Build the analysis specification using method chaining:

```python
tree = (AnalysisTree()
    .split_by('df.Gender', label='gender')
    .split_by('df.Country', label='country')
    .analyze_by(
        mean_income=lambda df: np.mean(df.Income),
        count=lambda df: len(df)
    ))
```

The tree is just a data structure at this point - no computation happens.

### Phase 2: Execution

Execute the tree on data with `.run()`:

```python
result = tree.run(df)
```

**Execution Flow:**

1. `AnalysisTree.run(data)` - Entry point
   - Sets up default environment if needed
   - Counts entities using `count_or_length(data, self.id)`
   - Recursively calls `.run()` on contained nodes
   - Returns DataTree

2. `SplitNode.run(data, environ, id, _N)` - Data partitioning
   - If `expr`: Groups by boolean result (True/False groups)
   - If `kwexpr`: Creates named groups (may overlap or be non-exhaustive)
   - Recursively runs child nodes on each partition
   - Returns SplitDataNode with LvlDataNode instances

3. `AnalysisNode.run(data, environ, id, _N)` - Computation
   - Evaluates all analysis expressions using `scope_eval()`
   - Returns DataNode with computed summary statistics

4. `CrossAnalysisNode.run(data_dict, environ, id, _N)` - Cross-level comparison
   - Takes dict with "df" and "ref_df"
   - Uses `scope_cross_eval()` for evaluation
   - Returns DataNode with comparison results

## Expression Evaluation System

pyMyriad supports two ways to specify computations:

### 1. Lambda Functions (Recommended)

```python
tree.analyze_by(
    mean=lambda df: np.mean(df.Income),
    count=lambda df: len(df)
)
```

**Pros**: Type-safe, IDE-friendly, no import warnings

### 2. String Expressions

```python
tree.analyze_by(
    mean="np.mean(df.Income)",
    count="len(df)"
)
```

**Pros**: Can be serialized, stored, and dynamically generated

**Key Functions** (utils.py):

- `scope_eval(expr, df, environ)` - Evaluate string/callable with DataFrame
  - If string: Uses `eval()` with injected `df`, `np`, `pd` in scope
  - If callable: Calls with `df` as argument
  - Returns computed value

- `scope_cross_eval(expr, df, ref_df, environ)` - For cross-level comparisons
  - Provides both `df` and `ref_df` to expressions

- `get_top_globals()` - Auto-detect numpy/pandas from caller's globals
  - Avoids "name not defined" warnings for string expressions

**Environment Setup**:

```python
# Set default environment for all trees
AnalysisTree.set_default_environ({'np': np, 'pd': pd})

# Or pass per-run
result = tree.run(df, environ={'np': np, 'pd': pd, 'custom': value})
```

## Main Entry Points

### For Users

1. **AnalysisTree()** - Start building an analysis tree
2. **tree.run(df)** - Execute analysis on data
3. **simple_table(result)** - Convert results to pandas DataFrame
4. **gt_table(result)** - Generate formatted HTML table
5. **forest_plot(result)** - Create visualization

### For Developers

1. **utils.scope_eval()** - Core expression evaluator
2. **tabular.flatten()** - Convert DataTree to flat DataFrame
3. **analysis_tree.py** - All tree construction logic
4. **data_tree.py** - All result data structures

## Module Guide

### Core Modules

**`src/pyMyriad/analysis_tree.py`** (~800 lines)
- All construction classes: AnalysisTree, SplitNode, AnalysisNode, CrossAnalysisNode
- Tree building methods: split_by(), analyze_by(), etc.
- Execution logic: run() methods
- **Start here** to understand tree construction

**`src/pyMyriad/data_tree.py`** (~300 lines)
- All result classes: DataTree, SplitDataNode, LvlDataNode, DataNode
- Pretty-printing methods (__str__)
- Basic tree traversal utilities
- **Read after** understanding construction side

**`src/pyMyriad/utils.py`** (~200 lines)
- Expression evaluation: scope_eval(), scope_cross_eval()
- String conversion: analysis_to_string()
- Environment management: get_top_globals()
- Helper functions: count_or_length()
- **Critical** for understanding how expressions work

### Output Modules

**`src/pyMyriad/tabular.py`** (~400 lines)
- flatten()/tabulate() - Convert trees to DataFrames
- format_statistics() - Apply format strings to summaries
- Pivoting and reshaping utilities
- **Key** for exporting results

**`src/pyMyriad/listing.py`** (~600 lines)
- simple_table() - Basic DataFrame tables
- cascade_table() - Hierarchical tables
- gt_table() - Formatted HTML tables using great-tables
- **Main** user-facing table functions

**`src/pyMyriad/plots.py`** (~500 lines)
- forest_plot() - Forest plots for effect sizes
- distribution_plot() - Distribution visualizations
- Matplotlib/Seaborn integration
- **Main** user-facing plotting functions

**`src/pyMyriad/cli.py`**
- Command-line interface (minimal usage currently)

## Testing Patterns

### Test Organization

- `test_analysis_tree.py` - Node initialization, construction, error handling
- `test_run.py` - Execution with string/lambda expressions
- `test_tree_construction.py` - Tree building methods
- `test_data_tree.py` - Data structure validation
- `test_format_statistics.py` - Result formatting
- `test_listing.py`, `test_plot.py` - Table/plot generation
- `test_performance.py` - Performance benchmarks (marked, skipped by default)

### Testing Conventions

1. **Use pytest framework** with fixtures
2. **Test both expression forms**: String expressions and lambda functions
3. **Use simple DataFrames**: 2-6 rows are sufficient for most tests
4. **Environment setup**: Use `with_module()` context manager for imports
5. **Test tree construction and execution separately**

Example test pattern:
```python
def test_simple_split_and_analysis():
    df = pd.DataFrame({
        'A': [10, 20, 30, 40],
        'B': [1, 2, 1, 2]
    })
    
    # Test construction
    tree = AnalysisTree().split_by('df.B').analyze_by(
        mean=lambda df: np.mean(df.A)
    )
    assert len(tree) == 1  # One split node
    assert isinstance(tree[0], SplitNode)
    
    # Test execution
    result = tree.run(df)
    assert isinstance(result, DataTree)
    assert 'mean' in result['df.B']['1']['analysis'].summary
```

## Key Design Decisions

1. **Subclass built-in types**: AnalysisTree/SplitNode are lists, DataTree/SplitDataNode are dicts
   - Enables intuitive indexing and iteration
   - Slightly unconventional but pragmatic

2. **String expressions supported**: Despite eval() concerns
   - Enables serialization and dynamic generation
   - Useful for configuration-driven analyses
   - Lambda functions remain recommended for code

3. **Termination flag**: Controls whether further splits can be added after an analysis
   - Allows intermediate summarization with `summarize_by()` (non-terminating)
   - Regular `analyze_by()` terminates the branch

4. **Path tracking**: Every node knows its location in the tree
   - Enables reconstruct of hierarchical structures
   - Critical for table generation and visualization

5. **Flexible grouping**: `kwexpr` allows overlapping or non-exhaustive groups
   - More flexible than traditional groupby
   - Supports custom cohort definitions

## Common Patterns

### Pattern 1: Stratified Analysis
```python
tree = (AnalysisTree()
    .split_by('df.GroupVar')
    .analyze_by(mean=lambda df: np.mean(df.Value)))
```

### Pattern 2: Multi-level Stratification
```python
tree = (AnalysisTree()
    .split_by('df.Gender')
    .split_by('df.AgeGroup')
    .analyze_by(count=lambda df: len(df)))
```

### Pattern 3: Custom Groups
```python
tree = (AnalysisTree()
    .split_by(
        low='df.Income < 50000',
        high='df.Income >= 50000',
        label='income_level'
    )
    .analyze_by(median=lambda df: np.median(df.Income)))
```

### Pattern 4: Intermediate Summary
```python
tree = (AnalysisTree()
    .split_by('df.Gender')
    .summarize_by(group_mean=lambda df: np.mean(df.Score))  # Non-terminating
    .split_by('df.Country')  # Can continue splitting
    .analyze_by(final_mean=lambda df: np.mean(df.Score)))
```

### Pattern 5: Cross-level Comparison
```python
tree = (AnalysisTree()
    .split_by('df.Treatment')
    .cross_analyze_by(
        diff=lambda df, ref_df: np.mean(df.Outcome) - np.mean(ref_df.Outcome),
        ref_lvl='Control'
    ))
```

---

**See also**: 
- [README.md](README.md) for quick start and installation
- [docs/guides/](docs/guides/) for user guides and tutorials
- [examples/notebooks/](examples/notebooks/) for interactive examples
- [EXAMPLES_GUIDE.md](examples/EXAMPLES_GUIDE.md) for notebook quick reference

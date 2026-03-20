# Examples Guide

Quick reference for the Jupyter notebook tutorials in `examples/notebooks/`. Each notebook demonstrates specific features and patterns of pyMyriad.

## Notebook Overview

### [01_getting_started.ipynb](notebooks/01_getting_started.ipynb)

**Introduction to pyMyriad basics**

- Installing and importing pyMyriad
- Creating simple analysis trees with single splits
- Understanding the construction → execution pattern
- Converting results to tables
- Basic DataFrame output

**Key concepts**: AnalysisTree, split_by(), analyze_by(), run(), simple_table()

**When to reference**: First-time users, basic tree construction, simple analyses

---

### [02_analysis_trees.ipynb](notebooks/02_analysis_trees.ipynb)

**Building complex hierarchical trees**

- Multi-level splits for stratified analysis
- Nested grouping (e.g., by gender, then by country)
- Understanding tree structure and paths
- Using both string expressions and lambda functions
- Intermediate vs terminal analyses

**Key concepts**: Nested splits, method chaining, split_at_by(), summarize_by(), termination

**When to reference**: Complex stratification, multi-level grouping, tree navigation

---

### [03_tables_and_listings.ipynb](notebooks/03_tables_and_listings.ipynb)

**Converting analysis results to formatted tables**

- Using simple_table() for basic DataFrames
- Creating cascade tables with hierarchical structure
- Generating HTML tables with gt_table()
- Pivoting and reshaping results
- Customizing table formatting

**Key concepts**: simple_table(), cascade_table(), gt_table(), pivoting, formatting

**When to reference**: Exporting results, creating reports, table customization

---

### [04_plots.ipynb](notebooks/04_plots.ipynb)

**Visualizing analysis results**

- Creating forest plots for effect sizes
- Distribution plots for raw data visualization
- Customizing plot aesthetics
- Handling multiple grouping levels in plots
- Integration with matplotlib/seaborn

**Key concepts**: forest_plot(), distribution_plot(), visualization patterns

**When to reference**: Creating plots, visual analytics, publication figures

---

### [05_formatting_statistics.ipynb](notebooks/05_formatting_statistics.ipynb)

**Formatting computed statistics for presentation**

- Applying format strings to summaries (e.g., "{mean:.2f}±{std:.2f}")
- Custom formatting functions
- Rounding and precision control
- Creating presentation-ready output
- Combining multiple statistics

**Key concepts**: format_statistics(), format strings, presentation output

**When to reference**: Report generation, formatting numbers, custom presentations

---

### [06_advanced_topics.ipynb](notebooks/06_advanced_topics.ipynb)

**Advanced features and patterns**

- Cross-level comparisons with cross_analyze_by()
- Custom grouping with kwexpr (overlapping/non-exhaustive groups)
- Environment management for expression evaluation
- Using split_at_by() for fine-grained tree control
- Performance considerations
- Edge cases and troubleshooting

**Key concepts**: CrossAnalysisNode, ref_lvl, kwexpr, environ, split_at_by()

**When to reference**: Advanced use cases, comparisons, custom workflows, performance optimization

---

## Quick Code Snippets by Task

### Basic Analysis
```python
# From: 01_getting_started.ipynb
tree = (AnalysisTree()
    .split_by('df.Gender')
    .analyze_by(
        mean=lambda df: np.mean(df.Income),
        count=lambda df: len(df)
    ))
result = tree.run(df)
```

### Multi-level Stratification
```python
# From: 02_analysis_trees.ipynb
tree = (AnalysisTree()
    .split_by('df.Gender')
    .split_by('df.Country')
    .split_by('df.AgeGroup')
    .analyze_by(median=lambda df: np.median(df.Salary)))
```

### Custom Groups
```python
# From: 06_advanced_topics.ipynb
tree = (AnalysisTree()
    .split_by(
        low='df.Income < 50000',
        mid='(df.Income >= 50000) & (df.Income < 100000)',
        high='df.Income >= 100000',
        label='income_bracket'
    )
    .analyze_by(count=lambda df: len(df)))
```

### Cross-level Comparison
```python
# From: 06_advanced_topics.ipynb
tree = (AnalysisTree()
    .split_by('df.Treatment')
    .cross_analyze_by(
        diff=lambda df, ref_df: np.mean(df.Outcome) - np.mean(ref_df.Outcome),
        pct_change=lambda df, ref_df: (np.mean(df.Outcome) / np.mean(ref_df.Outcome) - 1) * 100,
        ref_lvl='Control'
    ))
```

### Formatted Table
```python
# From: 03_tables_and_listings.ipynb
result = tree.run(df)
html_table = gt_table(
    result,
    title="Income Analysis by Demographics",
    subtitle="Data from 2024 Survey"
)
```

### Forest Plot
```python
# From: 04_plots.ipynb
forest_plot(
    result,
    x='effect_size',
    x_err='std_error',
    type='forest'
)
```

### Formatted Statistics
```python
# From: 05_formatting_statistics.ipynb
formatted = format_statistics(
    result,
    summary="{mean:.1f} ± {std:.1f}"
)
```

## Common Patterns Index

| Task | Notebook | Section |
|------|----------|---------|
| First-time setup | 01 | Getting Started |
| Simple split + analysis | 01 | Basic Trees |
| Multiple nested splits | 02 | Multi-level Analysis |
| String expressions | 02 | Expression Evaluation |
| Intermediate summaries | 02 | Non-terminating Nodes |
| Basic table output | 03 | Simple Tables |
| HTML tables | 03 | Great Tables |
| Pivot tables | 03 | Pivoting |
| Forest plots | 04 | Forest Plots |
| Distribution plots | 04 | Distributions |
| Format strings | 05 | Basic Formatting |
| Custom formatters | 05 | Advanced Formatting |
| Cross-comparisons | 06 | Cross-Analysis |
| Custom groups | 06 | Advanced Splitting |
| Environment setup | 06 | Expression Environment |
| Tree modification | 06 | split_at_by() |

## Learning Path

**For beginners**:
1. Start with 01_getting_started.ipynb
2. Progress to 02_analysis_trees.ipynb
3. Learn output with 03_tables_and_listings.ipynb

**For specific tasks**:
- **Tables/Reports**: Focus on 03_tables_and_listings.ipynb and 05_formatting_statistics.ipynb
- **Visualizations**: Jump to 04_plots.ipynb
- **Complex analyses**: Work through 02_analysis_trees.ipynb then 06_advanced_topics.ipynb

**For advanced users**:
- Go directly to 06_advanced_topics.ipynb for cross-analysis and custom grouping
- Review [ARCHITECTURE.md](../ARCHITECTURE.md) for implementation details

## Finding Examples

**By feature**:
- `split_by()` - Notebooks 01, 02, 06
- `analyze_by()` - All notebooks
- `summarize_by()` - Notebooks 02, 06
- `cross_analyze_by()` - Notebook 06
- `split_at_by()` - Notebook 06
- `simple_table()` - Notebooks 01, 03
- `gt_table()` - Notebook 03
- `forest_plot()` - Notebook 04
- `format_statistics()` - Notebook 05

**By data pattern**:
- Single grouping variable: Notebook 01
- Nested grouping: Notebook 02
- Custom/overlapping groups: Notebook 06
- Cross-group comparisons: Notebook 06

**By output format**:
- Pandas DataFrame: Notebooks 01, 03
- HTML table: Notebook 03
- Forest plot: Notebook 04
- Distribution plot: Notebook 04
- Formatted text: Notebook 05

## Tips for AI Agents

When searching for code examples:

1. **Start specific, go general**: Look for exact feature first (e.g., cross_analyze_by → Notebook 06), then check related patterns
2. **Check multiple notebooks**: Similar patterns may appear in different contexts
3. **Read notebook docstrings**: Each cell often has explanatory markdown
4. **Combine patterns**: Most real analyses combine techniques from multiple notebooks
5. **Refer to ARCHITECTURE.md**: For understanding *why* patterns work the way they do

## Running the Notebooks

```bash
# Install Jupyter
pip install jupyter

# Start Jupyter
cd examples/notebooks
jupyter notebook

# Or use VS Code Jupyter extension
```

Each notebook is self-contained with sample data and can be run independently.

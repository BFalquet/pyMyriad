---
name: add-analysis
description: Add a new analysis, table, or plot function to pyMyriad.
---

# Skill: Add a New Analysis Function

Use this skill when adding a public analysis, table, or plot function.

## Checklist

- [ ] Place the function in the correct module:
  - Construction logic → `src/pyMyriad/analysis_tree.py`
  - Result formatting → `src/pyMyriad/tabular.py`
  - Tables → `src/pyMyriad/listing.py`
  - Plots → `src/pyMyriad/plots.py`
- [ ] Export public symbols from `src/pyMyriad/__init__.py`.
- [ ] Use Google-style docstrings with `Args`, `Returns`, and `Example` sections.
- [ ] Include type hints for new public functions.
- [ ] Demonstrate both **construction** and **execution** in examples.
- [ ] Prefer lambda functions over string expressions in examples.
- [ ] Add at least one test in `tests/` covering both lambda and string expression forms.
- [ ] Run `pytest`, `ruff check`, and `pre-commit run --all-files`.
- [ ] Add a `CHANGELOG.md` entry under `[Unreleased]`.

## Example docstring shape

```python
def my_analysis(dtree: DataTree, ...) -> pd.DataFrame:
    """Short summary.

    Args:
        dtree: Result tree from ``AnalysisTree.run()``.
        ...

    Returns:
        A DataFrame containing ...

    Example:
        >>> tree = (AnalysisTree()
        ...     .split_by("df.Group")
        ...     .analyze_by(mean=lambda df: np.mean(df.Value)))
        >>> result = tree.run(df)
        >>> my_analysis(result)
    """
```

## See also

- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

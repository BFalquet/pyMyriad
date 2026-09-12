---
name: test
description: Write and run tests for pyMyriad.
---

# Skill: Testing in pyMyriad

Use this skill when adding or modifying tests in `tests/`.

## Quick commands

```bash
pytest                 # run the full suite
pytest -m performance  # run only performance tests
pytest -q              # short output
```

## Test data

Keep DataFrames small and explicit (2–6 rows). Example:

```python
df = pd.DataFrame({
    "A": [10, 20, 30, 40],
    "B": [1, 2, 1, 2],
})
```

## Test both expression forms

Any analysis function that accepts expressions must be tested with both lambdas and strings:

```python
def test_analysis_lambda(tree_builder):
    tree = AnalysisTree().analyze_by(mean=lambda df: np.mean(df.A))
    assert "mean" in tree.run(df)["analysis"].summary

def test_analysis_string(tree_builder):
    tree = AnalysisTree().analyze_by(mean="np.mean(df.A)")
    assert "mean" in tree.run(df)["analysis"].summary
```

## Standard test structure

1. Create a simple DataFrame.
2. Build the tree (test construction).
3. Run the tree on the DataFrame (test execution).
4. Assert on both structure and values.

## Performance tests

Mark expensive tests so they are skipped by default:

```python
@pytest.mark.performance
def test_large_dataset():
    ...
```

## See also

- [ARCHITECTURE.md](../ARCHITECTURE.md#testing-patterns)
- [CONTRIBUTING.md](../CONTRIBUTING.md#testing-conventions)

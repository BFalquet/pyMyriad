# Agent Instructions for pyMyriad

This repository uses standard agent entry points. If you are an AI coding assistant, read this file first, then follow the pointers to the canonical docs.

## Start here

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** — architectural overview: two-phase pattern (construction → execution), node classes, module responsibilities.
2. **[CONTRIBUTING.md](CONTRIBUTING.md)** — dev setup, branch/commit conventions, and PR workflow.
3. **[README.md](README.md)** — project overview and quick start.

## Quick verification

Run these before finishing work:

```bash
pytest                # full test suite
ruff check            # linting
pre-commit run --all-files
```

Tests use small explicit DataFrames (2–6 rows) and cover both lambda and string expression forms. See [`.agents/skills/test/SKILL.md`](.agents/skills/test/SKILL.md).

## Critical invariants

- `AnalysisTree` and `SplitNode` intentionally subclass `list`; `DataTree` and `SplitDataNode` intentionally subclass `dict`. Preserve these relationships.
- `AnalysisNode.termination` defaults to `True`. A terminated branch cannot accept further `split_by()` calls; use `summarize_by()` for non-terminating intermediate analyses.
- Prefer lambda functions over string expressions in examples and user-facing code.
- Every branch/PR must be tied to an issue; use branch naming like `feat/<issue-number>-short-description` and put `closes #<n>` in the PR description.

## Agent skills

Reusable workflows live in [`.agents/skills/`](.agents/skills/):

- [`test/`](.agents/skills/test/) — writing and running tests.
- [`pr-workflow/`](.agents/skills/pr-workflow/) — branch naming, pre-commit, PR description.
- [`add-analysis/`](.agents/skills/add-analysis/) — adding a new analysis/table/plot function.

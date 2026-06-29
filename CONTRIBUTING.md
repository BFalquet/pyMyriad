# Contributing to pyMyriad

Thank you for contributing! This guide covers everything needed to report issues, propose features, and submit pull requests.

## Reporting issues

Before opening a new issue, search existing ones to avoid duplicates.

Use the appropriate label:

| Label | When to use |
|---|---|
| `bug` | Something doesn't work as documented |
| `enhancement` | New feature or improvement to existing behaviour |
| `documentation` | Missing or incorrect docs |
| `clinical-reporting` | Specific to clinical/regulatory output formats |
| `ai-agents` | Relates to AI-assisted contribution workflows |

**For bugs** — include:
- Python version and pyMyriad version (`pip show pyMyriad`)
- Minimal reproducer (a few lines that trigger the issue)
- Actual vs. expected output

**For features** — link to a use case or clinical context (e.g. "needed for ICH E3 Table 14.1").

## Development setup

```bash
git clone https://github.com/BFalquet/pyMyriad.git
cd pyMyriade
pip install -e ".[docs]"
pre-commit install
pytest
```

`pip install -e ".[docs]"` installs all dev dependencies including `ruff` and `pre-commit`. Running `pre-commit install` wires up the ruff lint and format hooks so issues are caught before push.

## Branching and commits

Every branch should be tied to an issue.

**Branch naming:**

```
fix/<issue-number>-short-description
feat/<issue-number>-short-description
docs/<issue-number>-short-description
```

**Commit message style:** `<type>(<scope>): <description>`

```
feat(stats): add Wilson CI helper (#40)
fix(tabular): handle empty split levels (#38)
docs(contributing): add contribution guide (#50)
```

Reference the issue in commit messages with `refs #<n>` or `closes #<n>`.

## Pull requests

1. Open a **draft PR early** to signal work in progress.
2. Link the PR to its issue — put `closes #<n>` in the PR description so GitHub auto-closes the issue on merge.
3. Fill out every section of the PR template.
4. All CI checks must pass before requesting review.
5. Add a `CHANGELOG.md` entry under `[Unreleased]`.

## Testing conventions

- Use small, explicit DataFrames (2–6 rows) — see `CLAUDE.md` for the test structure pattern.
- Test both lambda and string expression forms for any analysis function.
- New public functions require at least one test; new modules require a dedicated test file.
- Run the full suite with `pytest` before pushing.

## Documentation conventions

- **Public functions**: Google-style docstrings with `Args`, `Returns`, and `Example` sections.
- **User-facing features**: update the relevant guide in `docs/guides/` or add an example notebook under `examples/`.
- **Architecture changes**: update `ARCHITECTURE.md` and `CLAUDE.md`.

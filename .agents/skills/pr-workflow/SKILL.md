---
name: pr-workflow
description: Prepare a branch and pull request for pyMyriad.
---

# Skill: PR Workflow in pyMyriad

Use this skill when starting work or opening a PR.

## Tie work to an issue

Every branch must be tied to an issue. Reference the issue in commits and PR descriptions with `refs #<n>` or `closes #<n>`.

## Branch naming

```
feat/<issue-number>-short-description
fix/<issue-number>-short-description
docs/<issue-number>-short-description
```

## Commit style

```
<type>(<scope>): <description>
```

Examples:

```
feat(stats): add Wilson CI helper (#40)
fix(tabular): handle empty split levels (#38)
```

## Before pushing

```bash
pytest
ruff check
pre-commit run --all-files
```

## Pull request

1. Open a draft PR early.
2. Put `closes #<n>` in the PR description.
3. Fill out every section of the PR template.
4. Add a `CHANGELOG.md` entry under `[Unreleased]`.
5. Ensure all CI checks pass before requesting review.

## See also

- [CONTRIBUTING.md](../CONTRIBUTING.md)

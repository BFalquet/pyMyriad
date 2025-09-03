



# README







## package creation

pyMyriade/
|
|--src/
|.  |--pyMyriade/
|.      |--__init__.py
|.      |--cli.py
|.      |--core.py
|
|--tests/
|.  |--__init__.py
|.  |--test_core.py
|
|--pyproject.toml
|--README.md
|--.gitignore
|--ruff.toml
|--uv.lock # dependency + env management


### dependencies

`uv` for package management
`pytest` for tests
`click` for cli
`ruff` for linting and formatting

### Procedure

```{bash}
uv init pyMyriade
cd pyMyriade
```




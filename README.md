# Book Tracker App

## Setup
For setup you need to do the following steps:
- For Linux/MacOS run `curl -sSL https://install.python-poetry.org | POETRY_VERSION=2.3.1 python3 -
`
- For Windows run `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -; POETRY_VERSION=2.3.1
`
If you already have potry installed ensure that it is of version 2.3.1, and if not run: `poetry self update 2.3.1`

- Make sure you use python 3.14
- Run `poetry install --with test_lint --no-root`

## Structure
- `src/backend` backend part with FastAPI
- `src/frontend` frontend part with streamlit
- `test` tests

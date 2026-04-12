# Book Tracker App

Book Tracker is a full-stack Python application for managing personal reading progress.

Tech stack:
- Backend: FastAPI + SQLite
- Frontend: Streamlit
- Testing and quality: pytest, pytest-cov, flake8, radon, bandit, locust

## Project Structure
- `src/backend` FastAPI backend
- `src/frontend` Streamlit frontend
- `test` unit and integration tests
- `locust` performance test scenarios

## Requirements
- Python `3.14`
- Poetry `2.3.1`

Install Poetry:
- Linux/macOS:
```bash
curl -sSL https://install.python-poetry.org | POETRY_VERSION=2.3.1 python3 -
```
- Windows (PowerShell):
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
poetry self update 2.3.1
```

Install dependencies:
```bash
poetry install --with test_lint --no-root
```

## Run Locally
Start backend:
```bash
poetry run uvicorn src.backend.app:app --reload --host 127.0.0.1 --port 8000
```

Start frontend (new terminal):
```bash
poetry run streamlit run src/frontend/app.py --server.port 8080
```

Application URLs:
- Frontend: `http://localhost:8080`
- Backend API: `http://localhost:8000`
- OpenAPI docs (Swagger): `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
## Results
- Radon: checks for cyclomatic complexity and maintainability index. We achieved `2.408` average cyclomatic complexity and average grade `A` on maintainability index.
- Flake8: no linter flags achieved.
- Pytest: `86.32%` test coverage achieved with `84` tests. All tests pass.
- Bandit: no vulnerabilities identified.
- Locust: response time `15ms` at P95 and `6ms` on average.

Then open:
- `http://localhost:8089`

Recommended check:
- P95 response time should be `< 200ms`

## API Endpoints (OpenAPI-backed)
Auth:
- `POST /auth/register`
- `POST /auth/login`

Books:
- `POST /books/`
- `GET /books/`
- `GET /books/{book_id}`
- `PUT /books/{book_id}`
- `DELETE /books/{book_id}`

System:
- `GET /`

## CI
CI workflow is configured in:
- `.github/workflows/test_lint.yml`

Current CI runs:
- `pytest --cov=src --cov-fail-under=70`
- `pytest test/`
- `radon cc -a -s src/`
- `radon mi -s src/`
- `flake8 src/`
- `bandit -r src/`

Note:
- Performance (`locust`) and OpenAPI completeness checks are currently non-blocking (not CI-gated).


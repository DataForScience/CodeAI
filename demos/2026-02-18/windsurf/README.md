# windsurf

This repository contains small demo modules for experimenting with Python tooling and simple API clients.

## Contents

- `demo1/`: A separate demo (has its own `README.md`).
- `demo2/`: A tiny `GitHubAPIClient` wrapper around the GitHub REST API.

## demo2: GitHub API client

`demo2/api_client.py` provides a `GitHubAPIClient` class with methods to fetch:

- The authenticated user (`GET /user`)
- Repositories visible to the authenticated user (`GET /user/repos`)
- A repository (`GET /repos/{owner}/{repo}`)
- Commits for a repo (`GET /repos/{owner}/{repo}/commits`)
- A specific commit (`GET /repos/{owner}/{repo}/commits/{sha}`)

Authentication is done via a GitHub personal access token (PAT) passed in the `Authorization` header.

## Setup

This project is managed with `uv`.

Install dependencies (including test deps):

```bash
uv sync --extra dev
```

## Running tests

Run the test suite:

```bash
uv run pytest
```

Run the suite with coverage (configured to run tests from `demo2/tests`):

```bash
uv run pytest --cov=demo2.api_client --cov-report=term-missing
```

## Running code

There is no CLI entrypoint in this repo. To use the client interactively:

```bash
uv run python
```

Then:

```python
from demo2.api_client import GitHubAPIClient

client = GitHubAPIClient(token="<YOUR_GITHUB_TOKEN>")
user = client.get_user()
repos = client.get_repositories()
```

Note: do not hardcode real tokens in committed code.

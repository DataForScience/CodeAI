# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup** (uses `uv` for dependency management):
```bash
uv sync          # install dependencies into .venv
```

**Run the scraper:**
```bash
uv run python scraper.py <url> [css-selector]
# Examples:
uv run python scraper.py https://news.ycombinator.com/ 'span.titleline a'
uv run python scraper.py https://example.com/ h1
```

**Run main entry point:**
```bash
uv run python main.py
```

**Auth via environment variables** (when running scraper against authenticated endpoints):
```bash
SCRAPER_USERNAME=user SCRAPER_PASSWORD=pass uv run python scraper.py <url>
SCRAPER_TOKEN=mytoken uv run python scraper.py <url>
SCRAPER_LOGIN_URL=https://... SCRAPER_USERNAME=user SCRAPER_PASSWORD=pass uv run python scraper.py <url>
```

## Architecture

- **Python 3.10**, managed with `uv` (`pyproject.toml` + `uv.lock`)
- **`scraper.py`** — core library module. `scrape_titles(url, selector, timeout, auth_config)` fetches a page and extracts text matching a CSS selector. `_build_session()` handles four auth strategies (basic, bearer, custom header, session/cookie login). Also runnable as a CLI script.
- **`main.py`** — placeholder entry point, currently prints "Hello from claude!"
- **`prompt1.txt` / `prompt2.txt`** — demo prompt files used during development sessions; not part of the runtime application.

## Dependencies

- `requests` — HTTP client
- `beautifulsoup4` — HTML parsing (uses `html.parser` backend, no lxml required)

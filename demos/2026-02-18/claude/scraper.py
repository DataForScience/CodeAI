"""Web scraper for extracting article titles from a given URL."""

import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, HTTPError, Timeout


def _build_session(auth_config: dict | None) -> requests.Session:
    session = requests.Session()
    if not auth_config:
        return session
    auth_type = auth_config.get("type")
    if auth_type == "basic":
        session.auth = HTTPBasicAuth(auth_config["username"], auth_config["password"])
    elif auth_type == "bearer":
        session.headers["Authorization"] = f"Bearer {auth_config['token']}"
    elif auth_type == "header":
        session.headers[auth_config["name"]] = auth_config["value"]
    elif auth_type == "session":
        session.post(auth_config["login_url"], data=auth_config["credentials"])
    return session


def scrape_titles(url: str, selector: str = "h2", timeout: int = 10, auth_config: dict | None = None) -> list[str]:
    """Fetch a webpage and extract text from elements matching a CSS selector.

    Args:
        url: The URL of the page to scrape.
        selector: CSS selector for title elements (default: "h2").
                  Examples: "h1", "h3", "span.titleline a", ".post-title"
        timeout: Request timeout in seconds.
        auth_config: Optional dict describing authentication. Supported types:
                     {"type": "basic", "username": "...", "password": "..."}
                     {"type": "bearer", "token": "..."}
                     {"type": "header", "name": "X-API-Key", "value": "..."}
                     {"type": "session", "login_url": "...", "credentials": {...}}

    Returns:
        A list of text content from all matched elements on the page.

    Raises:
        ValueError: If the URL is empty or invalid.
        ConnectionError: If the page cannot be reached.
        HTTPError: If the server returns an error status code.
        Timeout: If the request exceeds the timeout duration.
    """
    if not url or not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {url!r}")

    session = _build_session(auth_config)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    selectors = [selector, "span.titleline a"] if selector == "h2" else [selector]
    for sel in selectors:
        titles = [tag.get_text(strip=True) for tag in soup.select(sel)]
        if titles:
            return titles
    return []


if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scraper.py <url> [css-selector]")
        print("  css-selector defaults to 'h2'")
        print("  Example: python scraper.py https://news.ycombinator.com/ 'span.titleline a'")
        print("  Auth env vars: SCRAPER_USERNAME/SCRAPER_PASSWORD, SCRAPER_TOKEN, SCRAPER_LOGIN_URL")
        sys.exit(1)

    target_url = sys.argv[1]
    target_selector = sys.argv[2] if len(sys.argv) > 2 else "h2"

    username = os.environ.get("SCRAPER_USERNAME")
    password = os.environ.get("SCRAPER_PASSWORD")
    token = os.environ.get("SCRAPER_TOKEN")
    login_url = os.environ.get("SCRAPER_LOGIN_URL")

    target_auth = None
    if login_url and username and password:
        target_auth = {"type": "session", "login_url": login_url, "credentials": {"username": username, "password": password}}
    elif token:
        target_auth = {"type": "bearer", "token": token}
    elif username and password:
        target_auth = {"type": "basic", "username": username, "password": password}

    try:
        titles = scrape_titles(target_url, selector=target_selector, auth_config=target_auth)
        if titles:
            print(f"Found {len(titles)} title(s):")
            for title in titles:
                print(f"  - {title}")
        else:
            print(f"No elements matching {target_selector!r} found on the page.")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Timeout:
        print(f"Error: Request to {target_url!r} timed out.")
        sys.exit(1)
    except ConnectionError:
        print(f"Error: Could not connect to {target_url!r}.")
        sys.exit(1)
    except HTTPError as e:
        print(f"Error: Server returned {e.response.status_code} for {target_url!r}.")
        sys.exit(1)

"""Web scraper module for extracting article titles from web pages."""

import requests
from bs4 import BeautifulSoup
from typing import List

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

import logging
import argparse

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "MyScraper/1.0 (Educational; +https://example.com)"
}

def create_session() -> requests.Session:
    """Create a session with retry logic and exponential backoff."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,  # 1s, 2s, 4s between retries
        status_forcelist=[500, 502, 503, 504],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session

def scrape_article_titles(url: str) -> List[str]:
    """
    Extract all <h2> article titles from a given URL.
    
    Args:
        url: The URL of the web page to scrape.
        
    Returns:
        A list of strings containing the text of all <h2> elements found.
        
    Raises:
        requests.RequestException: When network or HTTP errors occur.
    """
    try:
        session = create_session()
        response = session.get(url, timeout=5, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise requests.RequestException("Request timed out. The server took too long to respond.")
    except requests.exceptions.ConnectionError:
        raise requests.RequestException("Connection failed. Check your internet connection or the URL.")
    except requests.exceptions.HTTPError as e:
        raise requests.RequestException(f"HTTP error occurred: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Network error: {e}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    # h2_elements = soup.find_all("h2")
    # titles = [h2.get_text(strip=True) for h2 in h2_elements]

    # For Hacker News specifically
    title_links = soup.select("span.titleline > a")
    titles = [a.get_text(strip=True) for a in title_links]

    logger.info("Fetching URL: %s", url)
    logger.debug("Found %d titles", len(titles))

    return titles

def main():
    parser = argparse.ArgumentParser(description="Extract article titles from a URL")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("-o", "--output", help="Output file path (optional)")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    titles = scrape_article_titles(args.url)
    for title in titles:
        print(title)

if __name__ == "__main__":
    main()
    

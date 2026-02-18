"""Web scraper module for extracting article titles from web pages."""

import requests
from bs4 import BeautifulSoup
from typing import List


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
        response = requests.get(url, timeout=10)
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

    return titles


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <URL>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    
    try:
        titles = scrape_article_titles(target_url)
        print(f"Found {len(titles)} article title(s):")
        for i, title in enumerate(titles, 1):
            print(f"  {i}. {title}")
    except requests.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)
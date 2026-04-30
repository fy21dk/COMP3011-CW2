# src/crawler.py



import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def fetch_page(url):
    """
    Fetch a single page and return its HTML content.

    Raises:
        requests.HTTPError: If the request fails.
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def parse_quotes(html, page_num):
    """
    Parse all quotes from a page.

    Returns:
        list[dict]: A list of quote dictionaries in this format:
        {
            "page": int,
            "quote_num": int,
            "text": str,
            "author": str,
            "tags": list[str],
        }
    """
    soup = BeautifulSoup(html, "html.parser")
    quote_blocks = soup.select("div.quote")

    quotes = []

    for i, block in enumerate(quote_blocks, start=1):
        text_tag = block.select_one("span.text")
        author_tag = block.select_one("small.author")
        tag_elements = block.select("div.tags a.tag")

        text = text_tag.get_text(strip=True) if text_tag else ""
        author = author_tag.get_text(strip=True) if author_tag else ""
        tags = [tag.get_text(strip=True) for tag in tag_elements]

        quotes.append({
            "page": page_num,
            "quote_num": i,
            "text": text,
            "author": author,
            "tags": tags,
        })

    return quotes


def get_next_page_url(html, current_url):
    """
    Find the next page URL from the current page HTML.

    Returns:
        str | None: The absolute URL of the next page, or None if there is no next page.
    """
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next a")

    if next_link is None:
        return None

    href = next_link.get("href")
    if not href:
        return None

    return urljoin(current_url, href)


def crawl_quotes(target_url, delay=6):
    """
    Crawl quotes starting from the given URL until no next page exists.

    Rules:
    - Follow the Next link until it disappears.
    - Wait at least `delay` seconds between page requests.

    Returns:
        list[dict]: All crawled quotes across all pages.
    """
    all_quotes = []
    current_url = target_url
    page_num = 1

    while current_url is not None:
        print(f"[INFO] Fetching page {page_num}: {current_url}")
        
        try:
            html = fetch_page(current_url)
        except Exception as e:
            print(f"[ERROR] Failed to fetch {current_url}: {e}")
            break

        quotes = parse_quotes(html, page_num)
        print(f"[INFO] Extracted {len(quotes)} quotes")
        
        # print("----- Test -----", type(quotes))
        # print(len(quotes))
        # print(quotes[:2])


        all_quotes.extend(quotes)

        next_url = get_next_page_url(html, current_url)

        if next_url is None:
            print("[INFO] No more pages. Crawling finished.")
            break

        print(f"[INFO] Waiting {delay} seconds before next request...\n")
        time.sleep(delay)
        current_url = next_url
        page_num += 1

    return all_quotes
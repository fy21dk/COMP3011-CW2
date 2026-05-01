# tests/test_crawler.py
# crawler.py unit tests
# Network requests and delays are mocked for stable testing.

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.crawler import (
    fetch_page,
    parse_quotes,
    get_next_page_url,
    crawl_quotes,
)


SAMPLE_HTML_PAGE_1 = """
<html>
    <body>
        <div class="quote">
            <span class="text">“Life is beautiful.”</span>
            <span>
                <small class="author">Mark Twain</small>
            </span>
            <div class="tags">
                <a class="tag">life</a>
                <a class="tag">inspirational</a>
            </div>
        </div>

        <div class="quote">
            <span class="text">“Art makes life meaningful.”</span>
            <span>
                <small class="author">Jane Austen</small>
            </span>
            <div class="tags">
                <a class="tag">art</a>
                <a class="tag">meaningful</a>
            </div>
        </div>

        <ul class="pager">
            <li class="next">
                <a href="/page/2/">Next <span aria-hidden="true">→</span></a>
            </li>
        </ul>
    </body>
</html>
"""


SAMPLE_HTML_PAGE_2 = """
<html>
    <body>
        <div class="quote">
            <span class="text">“The final page quote.”</span>
            <span>
                <small class="author">Albert Einstein</small>
            </span>
            <div class="tags">
                <a class="tag">final</a>
                <a class="tag">science</a>
            </div>
        </div>
    </body>
</html>
"""


def test_01_fetch_page_returns_html(monkeypatch):
    
    class MockResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            pass

    def mock_get(url, timeout=10):
        return MockResponse("<html><body>OK</body></html>")

    monkeypatch.setattr("src.crawler.requests.get", mock_get)

    html = fetch_page("http://example.com")
    assert html == "<html><body>OK</body></html>"


def test_02_parse_quotes_returns_quote_list():
    
    quotes = parse_quotes(SAMPLE_HTML_PAGE_1, page_num=1)

    assert len(quotes) == 2

    assert quotes[0]["page"] == 1
    assert quotes[0]["quote_num"] == 1
    assert quotes[0]["text"] == "“Life is beautiful.”"
    assert quotes[0]["author"] == "Mark Twain"
    assert quotes[0]["tags"] == ["life", "inspirational"]

    assert quotes[1]["page"] == 1
    assert quotes[1]["quote_num"] == 2
    assert quotes[1]["text"] == "“Art makes life meaningful.”"
    assert quotes[1]["author"] == "Jane Austen"
    assert quotes[1]["tags"] == ["art", "meaningful"]


def test_03_parse_quotes_empty_page():
    
    html = "<html><body><p>No quotes here.</p></body></html>"
    quotes = parse_quotes(html, page_num=1)

    assert quotes == []


def test_04_get_next_page_url_returns_absolute_next_url():
    next_url = get_next_page_url(
        SAMPLE_HTML_PAGE_1,
        "http://quotes.toscrape.com/",
    )

    assert next_url == "http://quotes.toscrape.com/page/2/"


def test_05_get_next_page_url_returns_none_when_missing():
    next_url = get_next_page_url(
        SAMPLE_HTML_PAGE_2,
        "http://quotes.toscrape.com/page/2/",
    )

    assert next_url is None


def test_06_crawl_quotes_follows_next_links(monkeypatch):
    pages = {
        "http://quotes.toscrape.com/": SAMPLE_HTML_PAGE_1,
        "http://quotes.toscrape.com/page/2/": SAMPLE_HTML_PAGE_2,
    }

    def mock_fetch_page(url):
        return pages[url]

    def mock_sleep(seconds):
        return None

    monkeypatch.setattr("src.crawler.fetch_page", mock_fetch_page)
    monkeypatch.setattr("src.crawler.time.sleep", mock_sleep)

    quotes = crawl_quotes("http://quotes.toscrape.com/", delay=6)

    assert len(quotes) == 3

    assert quotes[0]["page"] == 1
    assert quotes[0]["quote_num"] == 1
    assert quotes[1]["page"] == 1
    assert quotes[1]["quote_num"] == 2
    assert quotes[2]["page"] == 2
    assert quotes[2]["quote_num"] == 1
    assert quotes[2]["author"] == "Albert Einstein"


def test_07_crawl_quotes_single_page(monkeypatch):

    def mock_fetch_page(url):
        return SAMPLE_HTML_PAGE_2

    def mock_sleep(seconds):
        return None

    monkeypatch.setattr("src.crawler.fetch_page", mock_fetch_page)
    monkeypatch.setattr("src.crawler.time.sleep", mock_sleep)

    quotes = crawl_quotes("http://quotes.toscrape.com/", delay=6)

    assert len(quotes) == 1
    assert quotes[0]["page"] == 1
    assert quotes[0]["quote_num"] == 1
    assert quotes[0]["text"] == "“The final page quote.”"


def test_08_crawl_quotes_calls_sleep_between_pages(monkeypatch):

    pages = {
        "http://quotes.toscrape.com/": SAMPLE_HTML_PAGE_1,
        "http://quotes.toscrape.com/page/2/": SAMPLE_HTML_PAGE_2,
    }

    sleep_calls = []

    def mock_fetch_page(url):
        return pages[url]

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr("src.crawler.fetch_page", mock_fetch_page)
    monkeypatch.setattr("src.crawler.time.sleep", mock_sleep)

    crawl_quotes("http://quotes.toscrape.com/", delay=6)

    assert sleep_calls == [6]
    

def test_09_crawl_quotes_handles_fetch_error(monkeypatch):

    def mock_fetch_page(url):
        raise Exception("Network error")

    monkeypatch.setattr("src.crawler.fetch_page", mock_fetch_page)

    quotes = crawl_quotes("http://quotes.toscrape.com/", delay=6)

    assert quotes == []
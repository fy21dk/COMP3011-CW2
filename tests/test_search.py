# tests/test_search.py

import sys
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.search import (
    tokenize_query,
    make_snippet,
    get_matching_doc_ids,
    build_results,
    search,
    search_with_fallback,
)


@pytest.fixture
def sample_index():
    """
    Provide a small sample inverted index for testing.
    """
    return {
        "life": {
            "page1#q1": {
                "frequency": 1,
                "positions": [0],
                "fields": ["text", "tags"],
                "text": "Life is beautiful",
                "author": "Mark Twain",
            },
            "page2#q1": {
                "frequency": 1,
                "positions": [2],
                "fields": ["text"],
                "text": "Art makes life meaningful",
                "author": "Jane Austen",
            },
        },
        "mark": {
            "page1#q1": {
                "frequency": 0,
                "positions": [],
                "fields": ["author"],
                "text": "Life is beautiful",
                "author": "Mark Twain",
            }
        },
        "twain": {
            "page1#q1": {
                "frequency": 0,
                "positions": [],
                "fields": ["author"],
                "text": "Life is beautiful",
                "author": "Mark Twain",
            }
        },
        "beautiful": {
            "page1#q1": {
                "frequency": 1,
                "positions": [2],
                "fields": ["text"],
                "text": "Life is beautiful",
                "author": "Mark Twain",
            }
        },
        "inspirational": {
            "page1#q1": {
                "frequency": 0,
                "positions": [],
                "fields": ["tags"],
                "text": "Life is beautiful",
                "author": "Mark Twain",
            }
        },
    }


def test_01_tokenize_query_basic():
    """Test that query is tokenized into lowercase words."""
    assert tokenize_query("Mark Twain") == ["mark", "twain"]


def test_02_tokenize_query_with_punctuation():
    """Test that punctuation is removed."""
    assert tokenize_query(" Life, Beautiful! ") == ["life", "beautiful"]


def test_03_make_snippet_with_positions():
    """Test snippet generation using positions."""
    text = "Life is very beautiful and full of hope"
    snippet = make_snippet(text, [3], window=2)

    assert snippet == "is very beautiful and full"


def test_04_make_snippet_without_positions():
    """Test snippet fallback when no positions."""
    text = "Life is beautiful and inspiring"
    snippet = make_snippet(text, [])

    assert snippet == text


def test_05_get_matching_doc_ids_single_word(sample_index):
    """Test matching for a single word."""
    result = get_matching_doc_ids(sample_index, ["life"])
    assert result == {"page1#q1", "page2#q1"}


def test_06_get_matching_doc_ids_and_search(sample_index):
    """Test strict AND matching."""
    result = get_matching_doc_ids(sample_index, ["life", "mark"])
    assert result == {"page1#q1"}


def test_07_get_matching_doc_ids_missing_word(sample_index):
    """Test missing word returns empty."""
    result = get_matching_doc_ids(sample_index, ["life", "unknown"])
    assert result == set()


def test_08_build_results_basic(sample_index):
    """Test building results."""
    results = build_results(sample_index, ["life", "mark"], {"page1#q1"})

    assert len(results) == 1
    assert results[0]["doc_id"] == "page1#q1"
    assert results[0]["author"] == "Mark Twain"
    assert results[0]["frequency"] == 1
    assert sorted(results[0]["fields"]) == ["author", "tags", "text"]
    assert "Life" in results[0]["snippet"]


def test_09_search_single_word(sample_index):
    """Test search with one word."""
    results = search(sample_index, "life")
    assert len(results) == 2


def test_10_search_multiple_words_and(sample_index):
    """Test AND search."""
    results = search(sample_index, "life mark")

    assert len(results) == 1
    assert results[0]["doc_id"] == "page1#q1"


def test_11_search_author_word(sample_index):
    """Test author-based search."""
    results = search(sample_index, "mark")

    assert len(results) == 1
    assert "author" in results[0]["fields"]


def test_12_search_tags_word(sample_index):
    """Test tag-based search."""
    results = search(sample_index, "inspirational")

    assert len(results) == 1
    assert "tags" in results[0]["fields"]


def test_13_search_no_results(sample_index):
    """Test no results case."""
    assert search(sample_index, "life unknown") == []


def test_14_search_empty_query(sample_index):
    """Test empty query."""
    assert search(sample_index, "") == []


# -------------------------
# fallback search
# -------------------------

def test_15_fallback_strict_success(sample_index):
    """Test fallback returns strict result when possible."""
    results = search_with_fallback(sample_index, "life mark")

    assert results[0]["is_fallback"] is False
    assert results[0]["match_count"] == 2


def test_16_fallback_reduce_query(sample_index):
    """Test fallback reduces query size."""
    results = search_with_fallback(sample_index, "life mark unknown")

    assert results[0]["is_fallback"] is True
    assert results[0]["match_count"] == 2
    assert sorted(results[0]["matched_words"]) == ["life", "mark"]


def test_17_fallback_single_word(sample_index):
    """Test fallback to single word."""
    results = search_with_fallback(sample_index, "unknown twain")

    assert results[0]["match_count"] == 1
    assert results[0]["matched_words"] == ["twain"]


def test_18_fallback_no_match(sample_index):
    """Test fallback with no matches."""
    assert search_with_fallback(sample_index, "unknown missing") == []
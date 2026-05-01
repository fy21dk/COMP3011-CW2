# tests/test_search.py
# Search logic tests first.
# Basic main.py CLI regression tests are kept below.
# Output-format dependent tests are removed for final version.

import builtins
import importlib
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.search import search_with_fallback, make_snippet, search


# =========================
# search.py tests
# =========================
def test_01_search_with_fallback_deduplicates_results():
    index = {
        "good": {
            "page1#q1": {
                "frequency": 1,
                "positions": [0],
                "fields": ["text"],
                "text": "good friends matter",
                "author": "Author A",
            }
        },
        "friends": {
            "page1#q1": {
                "frequency": 1,
                "positions": [1],
                "fields": ["text"],
                "text": "good friends matter",
                "author": "Author A",
            }
        },
        "books": {
            "page1#q1": {
                "frequency": 1,
                "positions": [2],
                "fields": ["text"],
                "text": "good friends matter",
                "author": "Author A",
            }
        },
    }

    results = search_with_fallback(index, "good friends missing books")

    doc_ids = [item["doc_id"] for item in results]

    assert doc_ids.count("page1#q1") == 1
    assert len(results) == 1


def test_02_search_with_fallback_ranks_by_match_count_then_frequency():
    index = {
        "good": {
            "page1#q1": {
                "frequency": 1,
                "positions": [0],
                "fields": ["text"],
                "text": "good friends",
                "author": "Author A",
            },
            "page2#q1": {
                "frequency": 5,
                "positions": [0, 2, 4, 6, 8],
                "fields": ["text"],
                "text": "good good good good good",
                "author": "Author B",
            },
        },
        "friends": {
            "page1#q1": {
                "frequency": 1,
                "positions": [1],
                "fields": ["text"],
                "text": "good friends",
                "author": "Author A",
            }
        },
    }

    results = search_with_fallback(index, "good friends missing")

    assert len(results) >= 1

    assert results[0]["doc_id"] == "page1#q1"
    assert results[0]["match_count"] == 2
    assert results[0]["frequency"] == 2


def test_03_make_snippet_without_positions():
    text = "one two three four five six seven eight"

    snippet = make_snippet(text, positions=[])

    assert snippet == "one two three four five six"


def test_04_strictAND_distance_ranking():
    index = {
        "good": {
            "doc1": {
                "frequency": 1,
                "positions": [1],
                "fields": ["text"],
                "text": "good friends forever",
                "author": "A",
            },
            "doc2": {
                "frequency": 1,
                "positions": [1],
                "fields": ["text"],
                "text": "good very very friends",
                "author": "B",
            },
        },
        "friends": {
            "doc1": {
                "frequency": 1,
                "positions": [2],
                "fields": ["text"],
                "text": "good friends forever",
                "author": "A",
            },
            "doc2": {
                "frequency": 1,
                "positions": [4],
                "fields": ["text"],
                "text": "good very very friends",
                "author": "B",
            },
        },
    }

    results = search(index, "good friends")

    assert results[0]["doc_id"] == "doc1"
    assert results[1]["doc_id"] == "doc2"


# =========================
# main.py basic CLI tests
# =========================
@pytest.fixture
def main_module():
    """
    Import src.main fresh for each test.
    """

    import src.main as main
    return importlib.reload(main)

def test_11_main_loop_build_load_print_find_exit(monkeypatch, main_module, capsys):
    commands = iter([
        "build",
        "load",
        "print love",
        "find good friends",
        "exit",
    ])

    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(commands))

    calls = {
        "build": 0,
        "load": 0,
        "print": [],
        "find": [],
    }

    def fake_cmd_build():
        calls["build"] += 1

    def fake_cmd_load():
        calls["load"] += 1
        return {"loaded": True}

    def fake_cmd_print(index, word):
        calls["print"].append((index, word))

    def fake_cmd_find(index, query):
        calls["find"].append((index, query))

    monkeypatch.setattr(main_module, "cmd_build", fake_cmd_build)
    monkeypatch.setattr(main_module, "cmd_load", fake_cmd_load)
    monkeypatch.setattr(main_module, "cmd_print", fake_cmd_print)
    monkeypatch.setattr(main_module, "cmd_find", fake_cmd_find)

    main_module.main()

    assert calls["build"] == 1
    assert calls["load"] == 1
    assert calls["print"] == [({"loaded": True}, "love")]
    assert calls["find"] == [({"loaded": True}, "good friends")]

    captured = capsys.readouterr()
    assert "=== Simple Search Engine CLI ===" in captured.out
    assert "Commands: build, load, print <word>, find <query>, exit/quit" in captured.out
    assert "Bye." in captured.out


def test_12_main_loop_unknown_command(monkeypatch, main_module, capsys):
    commands = iter([
        "unknown",
        "exit",
    ])

    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(commands))

    main_module.main()

    captured = capsys.readouterr()
    assert "[ERROR] Unknown command." in captured.out
    assert "Available Commands: build, load, print <word>, find <query>, exit/quit" in captured.out


def test_13_main_loop_usage_errors(monkeypatch, main_module, capsys):
    commands = iter([
        "print",
        "find",
        "exit",
    ])

    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(commands))

    main_module.main()

    captured = capsys.readouterr()
    assert "[ERROR] Usage: print <word>" in captured.out
    assert "[ERROR] Usage: find <query>" in captured.out


def test_14_main_loop_empty_input_then_exit(monkeypatch, main_module, capsys):
    commands = iter([
        "",
        "   ",
        "exit",
    ])

    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(commands))

    main_module.main()

    captured = capsys.readouterr()
    assert "Bye." in captured.out
    
    


def test_21_get_index_path(main_module):
    path = main_module.get_index_path()

    assert path.name == "index.json"
    assert path.parent.name == "data"
    assert isinstance(path, Path)

'''
# CLI output format changes frequently
def test_22_cmd_build_calls_crawl_build_save(monkeypatch, tmp_path, capsys, main_module):
    fake_quotes = [
        {
            "page": 1,
            "quote_num": 1,
            "text": "hello world",
            "author": "tester",
            "tags": [],
        }
    ]
    fake_index = {"hello": {"page1#q1": {"frequency": 1}}}
    calls = {}

    fake_output = tmp_path / "data" / "index.json"

    def fake_get_index_path():
        return fake_output

    def fake_crawl_quotes(url, delay):
        calls["crawl"] = {"url": url, "delay": delay}
        return fake_quotes

    def fake_build_index(quotes):
        calls["build"] = quotes
        return fake_index

    def fake_save_index(index, path):
        calls["save"] = {"index": index, "path": path}

    monkeypatch.setattr(main_module, "get_index_path", fake_get_index_path)
    monkeypatch.setattr(main_module, "crawl_quotes", fake_crawl_quotes)
    monkeypatch.setattr(main_module, "build_index", fake_build_index)
    monkeypatch.setattr(main_module, "save_index", fake_save_index)

    main_module.cmd_build()

    assert calls["crawl"]["url"] == main_module.START_URL
    assert calls["crawl"]["delay"] == 6
    assert calls["build"] == fake_quotes
    assert calls["save"]["index"] == fake_index
    assert calls["save"]["path"] == str(fake_output)
    assert fake_output.parent.exists()

    captured = capsys.readouterr()
    assert "[INFO] Crawling..." in captured.out
    assert "[INFO] Building index..." in captured.out
    assert "[INFO] Saving index..." in captured.out
    assert "[INFO] Build complete." in captured.out
'''


def test_23_cmd_load_success(monkeypatch, tmp_path, capsys, main_module):
    fake_path = tmp_path / "data" / "index.json"
    fake_path.parent.mkdir(parents=True, exist_ok=True)
    fake_path.write_text("{}", encoding="utf-8")

    expected_index = {"love": {"page1#q1": {"frequency": 2}}}

    monkeypatch.setattr(main_module, "get_index_path", lambda: fake_path)
    monkeypatch.setattr(main_module, "load_index", lambda path: expected_index)

    result = main_module.cmd_load()

    assert result == expected_index

    captured = capsys.readouterr()
    assert "[INFO] Loading index..." in captured.out
    assert "[INFO] Index loaded." in captured.out


def test_24_cmd_load_missing_file(monkeypatch, tmp_path, capsys, main_module):
    missing_path = tmp_path / "data" / "index.json"

    monkeypatch.setattr(main_module, "get_index_path", lambda: missing_path)

    result = main_module.cmd_load()

    assert result is None

    captured = capsys.readouterr()
    assert "[ERROR] index.json not found. Run 'build' first." in captured.out


def test_25_cmd_print_requires_loaded_index(main_module, capsys):
    main_module.cmd_print(None, "love")

    captured = capsys.readouterr()
    assert "[ERROR] No index loaded. Use 'load' first." in captured.out


def test_26_cmd_print_word_not_found(main_module, capsys):
    index = {"life": {"page1#q1": {"frequency": 1}}}

    main_module.cmd_print(index, "love")

    captured = capsys.readouterr()
    assert "[INFO] 'love' not found." in captured.out

'''
# CLI output format changes frequently
def test_27_cmd_print_success(main_module, capsys):
    index = {
        "love": {
            "3-1": {
                "frequency": 2,
                "positions": [0, 5],
                "fields": ["text", "tags"],
                "text": "love you love life",
                "author": "Pablo Neruda",
            }
        }
    }

    main_module.cmd_print(index, "love")

    captured = capsys.readouterr()
    assert "[INFO] Inverted index for 'love':" in captured.out
    assert "3-1" in captured.out
    assert "Pablo Neruda" in captured.out
'''

def test_28_cmd_find_requires_loaded_index(main_module, capsys):
    main_module.cmd_find(None, "good friends")

    captured = capsys.readouterr()
    assert "[ERROR] No index loaded. Use 'load' first." in captured.out


'''
# CLI output format changes frequently
def test_29_cmd_find_strict_and(monkeypatch, main_module, capsys):
    strict_results = [
        {
            "doc_id": "2-1",
            "author": "Marilyn Monroe",
            "fields": ["tags", "text"],
            "frequency": 4,
            "snippet": "good part is you get",
        }
    ]

    monkeypatch.setattr(main_module, "search", lambda index, query: strict_results)
    monkeypatch.setattr(main_module, "search_with_fallback", lambda index, query: [])

    main_module.cmd_find({"dummy": {}}, "good friends")

    captured = capsys.readouterr()
    assert "[INFO] Search mode: strict AND" in captured.out
    assert "[INFO] 1 result(s) found." in captured.out
    assert "2-1" in captured.out
    assert "Marilyn Monroe" in captured.out
    assert "snippet=good part is you get" in captured.out
'''

'''
# CLI output format changes frequently
def test_30_cmd_find_fallback(monkeypatch, main_module, capsys):
    fallback_results = [
        {
            "doc_id": "2-1",
            "author": "Marilyn Monroe",
            "fields": ["text"],
            "frequency": 3,
            "snippet": "true best friends in the",
            "matched_words": ["friends"],
            "match_count": 1,
            "is_fallback": True,
        }
    ]

    monkeypatch.setattr(main_module, "search", lambda index, query: [])
    monkeypatch.setattr(main_module, "search_with_fallback", lambda index, query: fallback_results)

    main_module.cmd_find({"dummy": {}}, "good xyz friends")

    captured = capsys.readouterr()
    assert "[INFO] Search mode: fallback" in captured.out
    assert "[INFO] 1 result(s) found." in captured.out
    assert "2-1" in captured.out
    assert "match_count=1" in captured.out
    assert "matched_words=friends" in captured.out
'''

def test_31_cmd_find_no_results(monkeypatch, main_module, capsys):
    monkeypatch.setattr(main_module, "search", lambda index, query: [])
    monkeypatch.setattr(main_module, "search_with_fallback", lambda index, query: [])

    main_module.cmd_find({"dummy": {}}, "no such phrase")

    captured = capsys.readouterr()
    assert "[INFO] No matching documents." in captured.out



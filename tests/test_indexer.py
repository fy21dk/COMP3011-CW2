# tests/test_indexer.py
# indexer logic tests first.
# Basic main.py CLI regression tests are kept below.
# Output-format dependent main.py tests are disabled for final version.

import sys
import builtins
import importlib
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.indexer import build_index, save_index, load_index

# =========================
# indexer.py tests
# =========================
def test_01_build_index_creates_inverted_index():
    quotes = [
        {
            "page": 1,
            "quote_num": 1,
            "text": "Life is beautiful life",
            "author": "Author A",
            "tags": ["life", "inspirational"],
        }
    ]

    index = build_index(quotes)

    assert "life" in index
    assert "beautiful" in index
    assert "author" in index
    assert "inspirational" in index

    assert "page1#q1" in index["life"]
    assert index["life"]["page1#q1"]["frequency"] >= 2


def test_02_build_index_uses_page_quote_doc_id():
    quotes = [
        {
            "page": 2,
            "quote_num": 1,
            "text": "Hello world",
            "author": "Tester",
            "tags": [],
        }
    ]

    index = build_index(quotes)

    assert "page2#q1" in index["hello"]


def test_03_build_index_stores_positions():
    quotes = [
        {
            "page": 1,
            "quote_num": 1,
            "text": "love life love",
            "author": "Tester",
            "tags": [],
        }
    ]

    index = build_index(quotes)

    assert index["love"]["page1#q1"]["positions"] == [0, 2]


def test_04_build_index_removes_stopwords():
    quotes = [
        {
            "page": 1,
            "quote_num": 1,
            "text": "the life is beautiful",
            "author": "Tester",
            "tags": [],
        }
    ]

    index = build_index(quotes)

    assert "life" in index
    assert "beautiful" in index
    assert "the" not in index
    assert "is" not in index


def test_05_save_and_load_index(tmp_path):
    index = {
        "life": {
            "page1#q1": {
                "frequency": 1,
                "positions": [0],
                "fields": ["text"],
                "text": "life",
                "author": "Author A",
            }
        }
    }

    file_path = tmp_path / "index.json"

    save_index(index, file_path)
    loaded_index = load_index(file_path)

    assert loaded_index == index
    

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
    assert "Commands: build, load, print <word>, find <query>, exit" in captured.out
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

    assert isinstance(path, Path)
    assert path.name == "index.json"
    assert path.parent.name == "data"



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

    assert calls["crawl"]["url"] == main_module.TARGET_URL
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


def test_27_cmd_print_success(main_module, capsys):
    index = {
        "love": {
            "page3#q1": {
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

    assert "[INFO] Inverted index for 'love'" in captured.out
    assert "doc_id    : page3#q1" in captured.out
    assert "author    : Pablo Neruda" in captured.out
    assert "frequency : 2" in captured.out
    assert "fields    : text, tags" in captured.out
    assert "positions : page 3 - quote 1 - [0, 5]" in captured.out
    assert "url       : http://quotes.toscrape.com/page/3/" in captured.out


def test_28_cmd_find_requires_loaded_index(main_module, capsys):
    main_module.cmd_find(None, "good friends")

    captured = capsys.readouterr()
    assert "[ERROR] No index loaded. Use 'load' first." in captured.out


def test_29_cmd_find_strict_and(monkeypatch, main_module, capsys):
    strict_results = [
        {
            "doc_id": "page2#q1",
            "author": "Marilyn Monroe",
            "fields": ["text"],
            "frequency": 4,
            "strict_score": 3,
            "snippet": "good part is you get",
        }
    ]

    monkeypatch.setattr(
        main_module,
        "search",
        lambda index, query: strict_results
    )

    main_module.cmd_find({"dummy": {}}, "good friends")

    captured = capsys.readouterr()

    assert "[INFO] Search mode: strict AND" in captured.out
    assert "[INFO] 1 result(s) found." in captured.out
    assert "location : page 2 - quote 1 (page2#q1)" in captured.out
    assert "author   : Marilyn Monroe" in captured.out
    assert "score    : 3" in captured.out
    assert "fields   : text" in captured.out
    assert "snippet  : good part is you get" in captured.out
    assert "url      : http://quotes.toscrape.com/page/2/" in captured.out


def test_30_cmd_find_fallback(monkeypatch, main_module, capsys):
    fallback_results = [
        {
            "doc_id": "page2#q1",
            "author": "Marilyn Monroe",
            "fields": ["text"],
            "frequency": 3,
            "snippet": "true best friends in the",
            "matched_words": ["friends"],
            "match_count": 1,
            "is_fallback": True,
        }
    ]

    monkeypatch.setattr(
        main_module,
        "search",
        lambda index, query: []
    )
    monkeypatch.setattr(
        main_module,
        "search_with_fallback",
        lambda index, query: fallback_results
    )

    main_module.cmd_find({"dummy": {}}, "good xyz friends")

    captured = capsys.readouterr()

    assert "[INFO] No exact AND match found for query: 'good xyz friends'" in captured.out
    assert "[INFO] Falling back to partial matching..." in captured.out
    assert "[INFO] Search mode: fallback" in captured.out
    assert "[INFO] 1 result(s) found." in captured.out
    assert "[INFO] Showing top 1 result(s)." in captured.out
    assert "location      : page 2 - quote 1 (page2#q1)" in captured.out
    assert "author        : Marilyn Monroe" in captured.out
    assert "score         : 13" in captured.out
    assert "matched_words : friends" in captured.out
    assert "match_count   : 1" in captured.out
    assert "frequency     : 3" in captured.out
    assert "fields        : text" in captured.out
    assert "snippet       : true best friends in the" in captured.out
    assert "url           : http://quotes.toscrape.com/page/2/" in captured.out
    

def test_31_cmd_find_no_results(monkeypatch, main_module, capsys):
    monkeypatch.setattr(main_module, "search", lambda index, query: [])
    monkeypatch.setattr(main_module, "search_with_fallback", lambda index, query: [])

    main_module.cmd_find({"dummy": {}}, "no such phrase")

    captured = capsys.readouterr()
    assert "[INFO] No matching documents." in captured.out


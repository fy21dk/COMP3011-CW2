# tests/test_indexer.py

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.indexer import (
    tokenize,
    make_doc_id,
    add_term,
    build_index,
    save_index,
    load_index,
)


def test_01_tokenize_basic():
    """
    Test that basic text is tokenized into lowercase words.
    """
    assert tokenize("Love is life.") == ["love", "is", "life"]


def test_02_tokenize_author_name():
    """
    Test that an author name is tokenized correctly.
    """
    assert tokenize("Mark Twain") == ["mark", "twain"]


def test_03_make_doc_id():
    """
    Test that doc_id is generated in the expected format.
    """
    assert make_doc_id(3, 2) == "page3#q2"


def test_04_add_term_text():
    """
    Test that adding a text term updates frequency, positions, and fields.
    """
    index = {}

    add_term(
        index=index,
        word="love",
        doc_id="page1#q1",
        field="text",
        text="Love is life",
        author="Mark Twain",
        position=0,
    )

    posting = index["love"]["page1#q1"]
    assert posting["frequency"] == 1
    assert posting["positions"] == [0]
    assert posting["fields"] == ["text"]
    assert posting["text"] == "Love is life"
    assert posting["author"] == "Mark Twain"


def test_05_add_term_author_does_not_increase_text_frequency():
    """
    Test that adding an author term does not increase text frequency.
    """
    index = {}

    add_term(
        index=index,
        word="mark",
        doc_id="page1#q1",
        field="author",
        text="Love is life",
        author="Mark Twain",
        position=None,
    )

    posting = index["mark"]["page1#q1"]
    assert posting["frequency"] == 0
    assert posting["positions"] == []
    assert posting["fields"] == ["author"]


def test_06_add_term_tags_does_not_increase_text_frequency():
    """
    Test that adding a tag term does not increase text frequency.
    """
    index = {}

    add_term(
        index=index,
        word="inspirational",
        doc_id="page1#q1",
        field="tags",
        text="Love is life",
        author="Mark Twain",
        position=None,
    )

    posting = index["inspirational"]["page1#q1"]
    assert posting["frequency"] == 0
    assert posting["positions"] == []
    assert posting["fields"] == ["tags"]


def test_07_add_term_combines_fields_without_duplicates():
    """
    Test that repeated field insertion does not create duplicate field names.
    """
    index = {}

    add_term(index, "love", "page1#q1", "text", "Love is life", "Mark Twain", 0)
    add_term(index, "love", "page1#q1", "tags", "Love is life", "Mark Twain", None)
    add_term(index, "love", "page1#q1", "tags", "Love is life", "Mark Twain", None)

    posting = index["love"]["page1#q1"]
    assert posting["frequency"] == 1
    assert posting["positions"] == [0]
    assert sorted(posting["fields"]) == ["tags", "text"]


def test_08_build_index_includes_text_author_and_tags():
    """
    Test that build_index includes tokens from text, author, and tags.
    """
    quotes = [
        {
            "page": 1,
            "quote_num": 1,
            "text": "Love is life",
            "author": "Mark Twain",
            "tags": ["inspirational", "life"],
        }
    ]

    index = build_index(quotes)

    assert "love" in index
    assert "is" in index
    assert "life" in index
    assert "mark" in index
    assert "twain" in index
    assert "inspirational" in index

    love_posting = index["love"]["page1#q1"]
    assert love_posting["frequency"] == 1
    assert love_posting["positions"] == [0]
    assert "text" in love_posting["fields"]

    mark_posting = index["mark"]["page1#q1"]
    assert mark_posting["frequency"] == 0
    assert mark_posting["positions"] == []
    assert mark_posting["fields"] == ["author"]

    inspirational_posting = index["inspirational"]["page1#q1"]
    assert inspirational_posting["frequency"] == 0
    assert inspirational_posting["positions"] == []
    assert inspirational_posting["fields"] == ["tags"]


def test_09_build_index_text_and_tags_can_share_same_word():
    """
    Test that the same word can appear in both text and tags.
    """
    quotes = [
        {
            "page": 1,
            "quote_num": 1,
            "text": "Life is good",
            "author": "Anonymous",
            "tags": ["life"],
        }
    ]

    index = build_index(quotes)

    posting = index["life"]["page1#q1"]
    assert posting["frequency"] == 1
    assert posting["positions"] == [0]
    assert sorted(posting["fields"]) == ["tags", "text"]


def test_10_save_and_load_index(tmp_path):
    """
    Test that an index can be saved to and loaded from JSON without changes.
    """
    index = {
        "love": {
            "page1#q1": {
                "frequency": 1,
                "positions": [0],
                "fields": ["text"],
                "text": "Love is life",
                "author": "Mark Twain",
            }
        }
    }

    file_path = tmp_path / "index.json"

    save_index(index, str(file_path))
    loaded = load_index(str(file_path))

    assert loaded == index


def test_debug_01_print_index_structure():
    """
    Print the built index structure for manual inspection.
    """
    quotes = [
        {
            "page": 1,
            "quote_num": 1,
            "text": "Love is life",
            "author": "Mark Twain",
            "tags": ["inspirational", "life"],
        }
    ]

    index = build_index(quotes)

    print("\nINDEX CONTENT:")
    for word, postings in index.items():
        print(f"{word} -> {postings}")


def test_debug_02_show_tmp_path(tmp_path):
    """
    Print the temporary path used during testing.
    """
    print("\nTMP PATH:", tmp_path)
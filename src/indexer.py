# src/indexer.py


import json
import re
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent


STOP_WORDS = {
    "the", "is", "a", "an", "of", "to", "and", "in", "on", "for",
    "with", "as", "by", "at", "from"
}

def tokenize_text(text: str) -> list[str]:
    """
    Convert text (or tags) into lowercase word tokens.

    Rules:
    - lowercase
    - remove stopword
    - keep only alphanumeric word chunks
    - simple and predictable for coursework use

    Examples:
        "Love is life." -> ["love", "life"]
    """
    if not text:
        return []
    
    tokens = re.findall(r"[a-z0-9]+", text.lower())

    return [t for t in tokens if t not in STOP_WORDS]

def tokenize_author(text: str) -> list[str]:
    """
    Convert author into lowercase word tokens.

    Rules:
    - lowercase

    Examples:
        "Mark Twain" -> ["mark", "twain"]
        "The Rock" -> ["The", "Rock"]

    """
    if not text:
        return []
 
    return re.findall(r"[a-z0-9]+", text.lower())


def make_doc_id(page_num: int, quote_num: int) -> str:
    """
    Create the document id in the required format.

    Example:
        page_num=3, quote_num=2 -> "page3#q2"
    """
    return f"page{page_num}#q{quote_num}"


def add_term(
    index: dict[str, dict[str, dict[str, Any]]],
    word: str,
    doc_id: str,
    field: str,
    text: str,
    author: str,
    position: int | None = None,
) -> None:
    """
    Add one token occurrence into the inverted index.

    Design rules:
    - index[word][doc_id] stores one posting
    - frequency counts text occurrences only
    - positions store text positions only
    - fields records where the token was found: text / author / tags
    - text and author are stored for result display

    Parameters:
        index: the whole inverted index
        word: token to add
        doc_id: quote-level document id
        field: one of "text", "author", "tags"
        text: original quote text
        author: original author string
        position: token position in text only; None for author/tags
    """
    if word not in index:
        index[word] = {}

    if doc_id not in index[word]:
        index[word][doc_id] = {
            "frequency": 0,
            "positions": [],
            "fields": [],
            "text": text,
            "author": author,
        }

    posting = index[word][doc_id]

    if field not in posting["fields"]:
        posting["fields"].append(field)

    if field == "text":
        posting["frequency"] += 1
        if position is not None:
            posting["positions"].append(position)


def build_index(quotes: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """
    Build the inverted index from crawled quote data.

    Expected quote structure per item:
        {
            "page": 1,
            "quote_num": 1,
            "text": "Love is life",
            "author": "Mark Twain",
            "tags": ["love", "life"]
        }

    Notes:
    - text tokens are indexed with frequency + positions
    - author tokens are indexed with fields only
    - tag tokens are indexed with fields only
    - if a token already appears in text, do not add "tags" for that token
    """
    index: dict[str, dict[str, dict[str, Any]]] = {}

    for quote in quotes:
        page_num = quote["page"]
        quote_num = quote["quote_num"]
        text = quote["text"]
        author = quote["author"]
        tags = quote.get("tags", [])

        doc_id = make_doc_id(page_num, quote_num)

        # 1) Index text tokens
        text_tokens = tokenize_text(text)
        text_token_set = set(text_tokens)

        for position, word in enumerate(text_tokens):
            add_term(
                index=index,
                word=word,
                doc_id=doc_id,
                field="text",
                text=text,
                author=author,
                position=position,
            )

        # 2) Index author tokens
        author_tokens = tokenize_author(author)
        for word in author_tokens:
            add_term(
                index=index,
                word=word,
                doc_id=doc_id,
                field="author",
                text=text,
                author=author,
                position=None,
            )

        # 3) Index tag tokens
        # Skip tag tokens that already appear in text
        for tag in tags:
            for word in tokenize_text(tag):
                if word in text_token_set:
                    continue

                add_term(
                    index=index,
                    word=word,
                    doc_id=doc_id,
                    field="tags",
                    text=text,
                    author=author,
                    position=None,
                )

    return index


def save_index(
    index: dict[str, dict[str, dict[str, Any]]],
    path: Optional[str] = None,
) -> None:
    """
    Save the inverted index to JSON.
    """
    if path is None:
        output_path = BASE_DIR / "data" / "index.json"
    else:
        output_path = Path(path)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(index, file, ensure_ascii=False, indent=2)


def load_index(path: Optional[str] = None) -> dict[str, dict[str, dict[str, Any]]]:
    """
    Load the inverted index from JSON.
    """
    if path is None:
        input_path = BASE_DIR / "data" / "index.json"
    else:
        input_path = Path(path)

    if not input_path.exists():
        raise FileNotFoundError(f"Index file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {input_path}") from e

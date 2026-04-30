# src/main.py

from pathlib import Path
from src.crawler import crawl_quotes
from src.indexer import build_index, save_index, load_index
from src.search import search, search_with_fallback

TARGET_URL = "http://quotes.toscrape.com/"


def get_index_path() -> Path:
    base_dir = Path(__file__).resolve().parent
    project_root = base_dir.parent
    return project_root / "data" / "index.json"


def cmd_build() -> None:
    output_path = get_index_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("[INFO] Crawling...")
    quotes = crawl_quotes(TARGET_URL, delay=6)

    print("[INFO] Building index...")
    index = build_index(quotes)

    print("[INFO] Saving index...")
    save_index(index, str(output_path))

    print("[INFO] Build complete.")


def cmd_load():
    path = get_index_path()

    if not path.exists():
        print("[ERROR] index.json not found. Run 'build' first.")
        return None

    print("[INFO] Loading index...")
    index = load_index(str(path))
    print("[INFO] Index loaded.")
    return index


def cmd_print(index, word):
    if index is None:
        print("[ERROR] No index loaded. Use 'load' first.")
        return

    word = word.lower()

    if word not in index:
        print(f"[INFO] '{word}' not found.")
        return

    print(f"[INFO] Inverted index for '{word}':\n")

    postings = index[word]

    sorted_postings = sorted(
        postings.items(),
        key=lambda item: item[1].get("frequency", 0),
        reverse=True
    )
    
    for doc_id, data in sorted_postings:
        print(f"doc_id: {doc_id}")
        print(f"  author: {data.get('author', '')}")
        print(f"  frequency: {data.get('frequency', 0)}")
        print(f"  fields: {', '.join(data.get('fields', []))}")
        print(f"  positions: {data.get('positions', [])}")
        print()


def cmd_find(index, query: str) -> None:
    if index is None:
        print("[ERROR] No index loaded. Use 'load' first.")
        return

    strict_results = search(index, query)
    if strict_results:
        print("[INFO] Search mode: strict AND")
        print(f"[INFO] {len(strict_results)} result(s) found.")

        for item in strict_results:
            print(f"- {item['doc_id']} | freq={item['frequency']} | author={item['author']}")
            print(f"  fields={', '.join(item['fields'])}")
            print(f"  snippet={item['snippet']}")
        return

    fallback_results = search_with_fallback(index, query)
    if fallback_results:
        print("[INFO] Search mode: fallback")
        print(f"[INFO] {len(fallback_results)} result(s) found.")

        for item in fallback_results:
            matched_words = ", ".join(item.get("matched_words", []))
            print(
                f"- {item['doc_id']} | match_count={item.get('match_count', 0)} "
                f"| freq={item['frequency']} | author={item['author']}"
            )
            print(f"  matched_words={matched_words}")
            print(f"  fields={', '.join(item['fields'])}")
            print(f"  snippet={item['snippet']}")
        return

    print("[INFO] No matching documents.")


def main():
    index = None

    print("=== Simple Search Engine CLI ===")
    print("Commands: build, load, print <word>, find <query>, exit")

    while True:
        raw = input("> ").strip()

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        command = parts[0].lower()

        if command == "exit":
            print("Bye.")
            break

        elif command == "build":
            cmd_build()

        elif command == "load":
            index = cmd_load()

        elif command == "print":
            if len(parts) < 2:
                print("[ERROR] Usage: print <word>")
                continue
            cmd_print(index, parts[1])

        elif command == "find":
            if len(parts) < 2:
                print("[ERROR] Usage: find <query>")
                continue
            cmd_find(index, parts[1])

        else:
            print("[ERROR] Unknown command.")
            print("Available commands: build, load, print <word>, find <query>, exit")


if __name__ == "__main__":
    main()
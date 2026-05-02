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
    print()


def cmd_load():
    path = get_index_path()

    if not path.exists():
        print("[ERROR] index.json not found. Run 'build' first.")
        print()
        return None

    print("[INFO] Loading index...")
    index = load_index(str(path))
    print("[INFO] Index loaded.")
    print()
    
    return index


def cmd_print(index, word):
    if index is None:
        print("[ERROR] No index loaded. Use 'load' first.")
        print()
        return

    word = word.lower()

    if word not in index:
        print(f"[INFO] '{word}' not found.")
        print()
        return

    postings = index[word]

    sorted_postings = sorted(
        postings.items(),
        key=lambda item: item[1].get("frequency", 0),
        reverse=True
    )
    
    print(f"[INFO] Inverted index for '{word}' ({len(sorted_postings)} posting(s)):\n")

    
    for i, (doc_id, data) in enumerate(sorted_postings, 1):
        
        
        print(f"{i}.")
        print(f"  doc_id    : {doc_id}")
        print(f"  author    : {data.get('author', '')}")
        print(f"  frequency : {data.get('frequency', 0)}")
        print(f"  fields    : {', '.join(data.get('fields', []))}")
        
        page_part, quote_part = doc_id.split("#")
        page_num = page_part.replace("page", "")
        quote_num = quote_part.replace("q", "")
        print(
            f"  positions : page {page_num} - "
            f"quote {quote_num} - "
            f"{data.get('positions', [])}"
        )
        print(f"  url       : {make_url(doc_id)}")
        print()


def cmd_find(index, query: str) -> None:
    if index is None:
        print("[ERROR] No index loaded. Use 'load' first.")
        print()
        return

    strict_results = search(index, query)
    if strict_results:
        print("[INFO] Search mode: strict AND")
        print(f"[INFO] {len(strict_results)} result(s) found.\n")

        for i, item in enumerate(strict_results, 1):
            print(f"{i}.")

            page_part, quote_part = item['doc_id'].split("#")
            page_num = page_part.replace("page", "")
            quote_num = quote_part.replace("q", "")
            print(
                f"  location : "
                f"page {page_num} - quote {quote_num} "
                f"({item['doc_id']})"
            )
            print(f"  author   : {item['author']}")
            print(f"  score    : {item.get('strict_score', item['frequency'])}")
            print(f"  fields   : {', '.join(item['fields'])}")
            print(f"  snippet  : {item['snippet']}")
            print(f"  url      : {make_url(item['doc_id'])}")
            print()
            
        return

    fallback_results = search_with_fallback(index, query)
    if fallback_results:
        
        # No strict AND results -> fallback search
        print(f"[INFO] No exact AND match found for query: '{query}'")
        print("[INFO] Falling back to partial matching...\n")
    
        TOP_K = 3
        print("[INFO] Search mode: fallback")
        print(f"[INFO] {len(fallback_results)} result(s) found.\n")
        print(f"[INFO] Showing top {min(TOP_K, len(fallback_results))} result(s).\n")

        for i, item in enumerate(fallback_results[:TOP_K], 1):
            score = item.get("match_count", 0) * 10 + item.get("frequency", 0)
            matched_words = ", ".join(item.get("matched_words", []))
            
            print(f"{i}.")
            page_part, quote_part = item['doc_id'].split("#")
            page_num = page_part.replace("page", "")
            quote_num = quote_part.replace("q", "")
            print(
                f"  location      : "
                f"page {page_num} - quote {quote_num} "
                f"({item['doc_id']})"
            )
            print(f"  author        : {item['author']}")
            print(f"  score         : {score}")
            print(f"  matched_words : {matched_words}")
            print(f"  match_count   : {item.get('match_count', 0)}")
            print(f"  frequency     : {item['frequency']}")
            print(f"  fields        : {', '.join(item['fields'])}")
            print(f"  snippet       : {item['snippet']}")
            print(f"  url           : {make_url(item['doc_id'])}")
            print()
        return

    print("[INFO] No matching documents.")
    print()


def make_url(doc_id: str) -> str:
    page_num = doc_id.split("#")[0].replace("page", "")
    return f"http://quotes.toscrape.com/page/{page_num}/"


def main():
    index = None

    print("=== Simple Search Engine CLI ===")
    print("Commands: build, load, print <word>, find <query>, exit/quit")

    while True:
        raw = input("> ").strip()

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        command = parts[0].lower()

        if command in ("exit", "quit"):
            print("Bye.")
            print()
            break

        elif command == "build":
            cmd_build()

        elif command == "load":
            index = cmd_load()

        elif command == "print":
            if len(parts) < 2:
                print("[ERROR] Usage: print <word>")
                print()
                continue
            cmd_print(index, parts[1])

        elif command == "find":
            if len(parts) < 2:
                print("[ERROR] Usage: find <query>")
                print()
                continue
            cmd_find(index, parts[1])

        else:
            print("[ERROR] Unknown command.")
            print("Available Commands: build, load, print <word>, find <query>, exit/quit")
            print()


if __name__ == "__main__":
    main()
# src/amin.py


from pathlib import Path
from crawler import crawl_quotes
from indexer import build_index, save_index

start_url = "http://quotes.toscrape.com/"

def main():
    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BASE_DIR.parent

    output_path = PROJECT_ROOT / "data" / "index.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("[INFO] Starting crawler...")
    quotes = crawl_quotes(start_url, delay=6)
    print(f"[DEBUG] quotes collected: {len(quotes)}")

    print("[INFO] Building index...")
    index = build_index(quotes)
    print(f"[DEBUG] index size: {len(index)}")

    print("[INFO] Saving index.json...")
    print(f"[DEBUG] save path: {output_path}")

    save_index(index, str(output_path)) 

    print("[INFO] Done.")

if __name__ == "__main__":
    main()
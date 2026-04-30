# COMP3011 Coursework 2: Search Engine Tool
This project implements a simple search engine that crawls quotes from a website, builds an inverted index, and provides a command-line interface (CLI) for searching.

---
## Project Structure
```
comp3011-cw2/
├── src/
│   ├── main.py        # CLI entry point
│   ├── crawler.py     # Web crawler (quotes.toscrape.com)
│   ├── indexer.py     # Inverted index builder
│   └── search.py      # Search logic (AND + fallback)
├── tests/
│   ├── test_crawler.py
│   ├── test_indexer.py
│   └── test_search.py
├── data/
│   └── index.json     # Saved inverted index
├── requirements.txt
└── README.md
```

---
## Setup
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---
## How to Run
```
python -m src.main
```

---
## CLI Commands
```
> build  
> load  
> print <word>  
> find <query>  
> exit  
```

---
## 🔎 Features

- Inverted index
- AND search
- Fallback search
- Snippet generation
- Author and tag search

---
## Testing
```
pytest tests -v
```

---
## 📦 Output

data/index.json

---
## 👨‍💻 Author
Dongwook Kim

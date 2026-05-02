# COMP3011 Coursework 2: Search Engine Tool
This project implements a simple search engine for the website:

https://quotes.toscrape.com/

The tool crawls quote pages, builds an inverted index, and provides a command-line interface (CLI) for searching and retrieving quote information.

---
## Features
* Web crawler using Requests and BeautifulSoup
* Inverted index generation
* Word frequency and position tracking
* Stopword removal
* Case-insensitive search
* Author and tag keyword indexing
* Strict AND search with distance-based ranking
* Fallback search ranking when strict AND fails
* Snippet generation
* JSON-based index storage
* Pytest-based unit tests

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
Create a virtual environment and install dependencies:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---
## How to Run
The project is organised as a Python package structure under the `src` directory.

Run the CLI using:

`python -m src.main`


---
## CLI Commands
```
> build
> load
> print <word>
> find <query>
> exit / quit
```

### Build the index
`> build`

Crawls all pages from the target website and saves the generated inverted index into:

`data/index.json`

### Load the index
`> load`

Loads the saved index from disk.

### Print a word entry
`> print <word>`

Display inverted index postings for a specific word.

Example: `print nonsense`

output: `positions : page 2 - quote 1 - [0, 3]`


### Search for documents
`> find <query>`

Search quotes using strict AND search with fallback ranking.

The search process works as follows:
1. Try strict AND search first.
2. If no strict AND results are found, perform fallback search using partial query matching.


Example: `> find good friends`

output: `location : page 2 - quote 1 (page2#q1)`

In strict AND search, results are ranked by the positional distance between query words.<br>
A lower score means the query words appear closer together in the quote.

For single-word queries, strict AND score is the same for all matches, so results are ranked by frequency.

---
## Design Decisions

### Inverted Index
The inverted index is implemented using nested Python dictionaries.

Each word stores:
* document ID
* frequency
* positions
* fields
* original quote text
* author

Example document ID format: `page2#q1`

### Search Strategy

The search engine uses:

1. Strict AND search
2. Fallback ranking search

Fallback ranking score: 

`match_count * 10 + frequency`

This prioritises documents matching more query words.

### Politeness Window

The crawler respects a 6-second politeness delay between requests as required by the coursework specification.

---
## Testing

Tests use mocking and monkeypatching to isolate crawler, search, and CLI behaviours.

The project includes unit tests for:
* crawler
* indexer
* search

Run all tests:

`pytest tests -v`

Run a specific test file:
```
pytest tests/test_indexer.py -v
pytest tests/test_crawler.py -v
pytest tests/test_search.py -v
```


---
## GenAI Usage

ChatGPT was used during development for:

* debugging
* test refinement
* CLI structure discussion
* search ranking ideas

All generated suggestions were manually reviewed and modified where necessary.

---
## 👨‍💻 Author
Dongwook Kim, 
fy21dk@leeds.ac.uk

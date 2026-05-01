# src/search.py

import re
from itertools import combinations


def tokenize_query(query):
    """
    Convert a raw query string into a list of lowercase tokens.

    Example:
        "Mark Twain" -> ["mark", "twain"]
    """
    return re.findall(r"[a-z0-9]+", query.lower())


def make_snippet(text, positions, window=3):
    """
    Generate a snippet from the text based on positions.

    Rules:
    - If positions exist, use the first position and include surrounding words.
    - If no positions, return the beginning of the text.
    """
    words = text.split()

    if not words:
        return ""

    if not positions:
        return " ".join(words[: min(len(words), 6)])

    pos = positions[0]
    start = max(0, pos - window)
    end = min(len(words), pos + window + 1)

    return " ".join(words[start:end])


def get_matching_doc_ids(index, words):
    """
    Return the intersection of doc_id sets for all query words.

    This implements strict AND search.
    """
    if not words:
        return set()

    doc_sets = []

    for word in words:
        if word not in index:
            return set()
        doc_sets.append(set(index[word].keys()))

    return set.intersection(*doc_sets)



def calculate_strictAND_score(query_terms, doc_positions):
    """
    Perform strict AND search with distance-based ranking.

    Ranking strategy:
    1. All query terms must exist in the same document.
    2. Documents are ranked by positional proximity of query terms.
    3. Smaller distance between query words gives higher score.
    4. Exact phrase matches receive the best ranking.
    """
    
    total_distance = 0

    for i in range(len(query_terms) - 1):
        left_positions = doc_positions.get(query_terms[i], [])
        right_positions = doc_positions.get(query_terms[i + 1], [])

        if not left_positions or not right_positions:
            return 0

        min_distance = min(
            abs(left - right)
            for left in left_positions
            for right in right_positions
        )

        total_distance += min_distance

    return 1000 - total_distance



def build_results(index, words, matched_doc_ids):
    """
    Build the final search results list from matched doc_ids.

    This function is shared by both strict search and fallback search.
    """
    results = []

    for doc_id in matched_doc_ids:
        total_frequency = 0
        merged_fields = set()
        text = ""
        author = ""
        snippet_positions = []
        doc_positions = {}

        for word in words:
            posting = index[word][doc_id]

            doc_positions[word] = posting["positions"]

            total_frequency += posting["frequency"]
            merged_fields.update(posting["fields"])

            if not text:
                text = posting["text"]
            if not author:
                author = posting["author"]

            if posting["positions"] and not snippet_positions:
                snippet_positions = posting["positions"]

        snippet = make_snippet(text, snippet_positions)
        strict_score = calculate_strictAND_score(words, doc_positions)

        results.append({
            "doc_id": doc_id,
            "author": author,
            "text": text,
            "fields": sorted(merged_fields),
            "frequency": total_frequency,
            "snippet": snippet,
            "strict_score": strict_score,
        })

    results.sort(
        key=lambda item: (
            -item["strict_score"],
            -item["frequency"],
            item["doc_id"]
        )
    )

    return results


def search(index, query):
    """
    Perform strict AND search.

    - All query words must be present in the document.
    - If no results, return an empty list.
    """
    words = tokenize_query(query)
    if not words:
        return []

    matched_doc_ids = get_matching_doc_ids(index, words)
    if not matched_doc_ids:
        return []

    return build_results(index, words, matched_doc_ids)


def search_with_fallback(index, query):
    """
    Perform search with fallback strategy.

    Steps:
    1. Try strict AND search.
    2. If no results, try smaller combinations of query words.
    3. Prefer results with more matched words.
    """
    words = tokenize_query(query)
    if not words:
        return []

    # Step 1: strict AND search
    strict_results = search(index, query)
    if strict_results:
        for item in strict_results:
            item["matched_words"] = words
            item["match_count"] = len(words)
            item["is_fallback"] = False
        return strict_results

    # Step 2: fallback with smaller combinations
    for size in range(len(words) - 1, 0, -1):
        fallback_results = []

        for combo in combinations(words, size):
            combo_words = list(combo)
            matched_doc_ids = get_matching_doc_ids(index, combo_words)

            if not matched_doc_ids:
                continue

            combo_results = build_results(index, combo_words, matched_doc_ids)

            for item in combo_results:
                item["matched_words"] = combo_words
                item["match_count"] = size
                item["is_fallback"] = True

            fallback_results.extend(combo_results)

        if fallback_results:
            # Deduplicate results by doc_id, keeping the best match
            best_by_doc_id = {}

            for item in fallback_results:
                doc_id = item["doc_id"]

                if doc_id not in best_by_doc_id:
                    best_by_doc_id[doc_id] = item
                    continue

                current = best_by_doc_id[doc_id]

                # Prefer higher match_count
                if item["match_count"] > current["match_count"]:
                    best_by_doc_id[doc_id] = item
                # If equal, prefer higher frequency
                elif item["match_count"] == current["match_count"]:
                    if item["frequency"] > current["frequency"]:
                        best_by_doc_id[doc_id] = item

            final_results = list(best_by_doc_id.values())
            final_results.sort(
                key=lambda item: (-item["match_count"], -item["frequency"], item["doc_id"])
            )
            return final_results

    return []


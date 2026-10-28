"""Keyword scoring (BM25) for the twin's hybrid search.

The embedding model ranks Persian chunks poorly: for "automation" in Persian the
n8n chunk came 7th although the word is in its heading (probe, 2026-10-28).
Exact words fix that, and rare words weigh more than words found everywhere.
"""

import math
import re
from collections import Counter

K1 = 1.2
B = 0.75
# idf of a word in about one doc in eight; rarer words count as topic words.
RARE_IDF = 2.0
ARABIC = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه"})


def tokens(text: str) -> list[str]:
    """Lowercase words with Arabic letter forms unified to Persian ones."""
    return re.findall(r"\w+", text.lower().translate(ARABIC))


def idf(n: int, total: int) -> float:
    """How rare a word found in n of total docs is (BM25 form, never negative)."""
    return math.log(1 + (total - n + 0.5) / (n + 0.5))


def bm25_scores(question: str, docs: list[str]) -> list[float]:
    """BM25 score of each doc for the question; 0 means no shared word."""
    bags = [Counter(tokens(d)) for d in docs]
    avg = sum(sum(b.values()) for b in bags) / len(bags)
    words = set(tokens(question))
    weight = {w: idf(sum(1 for b in bags if w in b), len(bags)) for w in words}
    scores = []
    for bag in bags:
        length = sum(bag.values())
        score = 0.0
        for word in words:
            if tf := bag[word]:
                norm = tf + K1 * (1 - B + B * length / avg)
                score += weight[word] * tf * (K1 + 1) / norm
        scores.append(score)
    return scores


def rare_words(question: str, docs: list[str]) -> set[str]:
    """Question words found in at most about one doc in eight.

    Such a word means the knowledge does mention the topic, even when the
    meaning search finds every chunk far away ("data science" in Persian
    was handed off at distance 0.803, 2026-10-28).
    """
    bags = [set(tokens(d)) for d in docs]
    found = {w: sum(1 for b in bags if w in b) for w in set(tokens(question))}
    return {w for w, n in found.items() if n and idf(n, len(bags)) >= RARE_IDF}

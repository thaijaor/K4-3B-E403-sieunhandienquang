"""Module tìm kiếm và xếp hạng các đoạn nguồn (sources) trong bài học bằng BM25."""
import math
import re
from typing import Any

TOKEN_PATTERN = re.compile(r"[\w\d]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Tách từ đơn giản, chuyển về chữ thường."""
    if not text:
        return []
    return TOKEN_PATTERN.findall(text.lower())


class BM25:
    """Okapi BM25 đơn giản cho danh sách các đoạn trích trong bài học."""

    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lens = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_lens) / self.corpus_size if self.corpus_size > 0 else 1.0

        # Đếm document frequency (df) cho mỗi term
        self.df: dict[str, int] = {}
        for doc in corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self.df[term] = self.df.get(term, 0) + 1

        # Tính IDF: ln(1 + (N - n + 0.5) / (n + 0.5))
        self.idf: dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def score(self, query_tokens: list[str], doc_tokens: list[str], doc_len: int) -> float:
        if doc_len == 0:
            return 0.0
        score = 0.0
        term_freqs: dict[str, int] = {}
        for token in doc_tokens:
            term_freqs[token] = term_freqs.get(token, 0) + 1

        for q in query_tokens:
            if q not in term_freqs:
                continue
            tf = term_freqs[q]
            idf = self.idf.get(q, 0.0)
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
            score += idf * (numerator / denominator)
        return score


def search_sources(
    query: str,
    sources: list[dict[str, Any]],
    selected_ids: list[str] | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Tìm top_k đoạn nguồn liên quan nhất trong bài học.
    
    Ưu tiên các đoạn học viên đã chọn (selected_ids), sau đó xếp hạng bằng BM25.
    """
    if not sources:
        return []

    selected_ids = selected_ids or []
    query_tokens = tokenize(query)

    # Chuẩn bị corpus: tiêu đề nhân đôi trọng số để tăng độ khớp
    corpus: list[list[str]] = []
    for s in sources:
        title_tokens = tokenize(s.get("title", ""))
        text_tokens = tokenize(s.get("text", ""))
        corpus.append(title_tokens + title_tokens + text_tokens)

    bm25 = BM25(corpus)

    # Tính điểm từng đoạn
    scored: list[tuple[float, int, dict[str, Any]]] = []
    for idx, s in enumerate(sources):
        sc = bm25.score(query_tokens, corpus[idx], len(corpus[idx]))
        # Ưu tiên cộng điểm nếu đoạn nằm trong selected_ids
        if s.get("id") in selected_ids:
            sc += 100.0
        scored.append((sc, idx, s))

    # Sắp xếp theo điểm giảm dần
    scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)

    # Lấy top_k
    result: list[dict[str, Any]] = []
    for sc, _, s in scored[:top_k]:
        result.append(s)

    return result

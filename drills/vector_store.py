#!/usr/bin/env python3
"""Exact against approximate search, and hybrid against either half.

    python3 drills/vector_store.py

The `vector-stores` page demonstrates the ranking half of the subject: BM25, a
deterministic stand-in for dense retrieval, and reciprocal rank fusion over a
hand-built corpus of eight chunks. It does not demonstrate the half the store
itself exists for, which is the approximate-nearest-neighbour tradeoff: a
vector store is interesting precisely because it does not compare the query to
every vector, and what it gives up for that is recall.

This drill measures that tradeoff on a corpus large enough for it to exist,
then measures whether hybrid retrieval beats either half on a query mix that
contains both kinds of question.

## What the vectors are, and are not

They are **hashed, not learned**. Each chunk's tokens are hashed into a fixed
number of dimensions with a signed hash, and the result is L2-normalised. No
model, no weights, no training, and nothing downloaded.

What that substitution preserves is everything this drill measures. Exact
search is exact for any vectors; IVF's recall loss comes from the geometry of
clustering a set of points and probing only some clusters, which is a property
of the points rather than of where they came from; and hashing collisions blur
distinct tokens into one dimension, which is structurally the same failure a
real embedding model has when it blurs `max_memory_gb` into `max_memory_mb`.

What it does not preserve is semantics. Hashed vectors have no notion that
"turn the cache off" and `cache=False` are related, so this drill cannot and
does not make any claim about dense retrieval quality. The paraphrase queries
below are matched by hashing a cue term, which is a stand-in for semantic
similarity and not an instance of it. For a quality comparison, run the
`embeddings` golden path against a real model.

The recall and latency numbers are therefore real measurements of a real
index, and the quality numbers are a measurement of this corpus's construction.
Both are labelled as such below.
"""

from __future__ import annotations

import hashlib
import math
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass

import numpy as np

DIMENSIONS = 64
CORPUS_SIZE = 4000
NLIST = 64
TOP_K = 10
RRF_K = 60
SEED = 20261102

#: Vocabulary for the synthetic corpus. Split deliberately: identifiers are
#: the tokens lexical search is good at, and topics are what a paraphrase
#: query has instead of them.
IDENTIFIERS = [
    f"{prefix}_{suffix}"
    for prefix in ("batch", "max_memory", "cache", "retry", "timeout", "pool", "stream")
    for suffix in ("size", "gb", "mb", "ms", "limit", "budget", "mode")
]
TOPICS = {
    "latency": ["p99", "tail", "responsive", "slow", "wait", "deadline"],
    "throughput": ["throughput", "items", "rate", "saturate", "pipeline"],
    "memory": ["memory", "allocation", "footprint", "resident", "cap"],
    "caching": ["cache", "invalidate", "warm", "evict", "hit"],
    "errors": ["error", "exit", "invalid", "refused", "retry"],
    "config": ["default", "option", "client", "configure", "override"],
}
FILLER = [
    "the", "set", "on", "to", "when", "a", "value", "server", "request",
    "client", "see", "also", "note", "for", "this", "is", "and", "with",
]


def hashed_vector(tokens: list[str]) -> np.ndarray:
    """Feature-hash tokens into DIMENSIONS dims with a signed hash.

    The sign is taken from a different byte of the same digest than the index,
    so collisions cancel as often as they compound. Unsigned hashing makes
    every collision additive, which inflates similarity between unrelated
    chunks and would flatter the approximate index for the wrong reason.
    """
    vector = np.zeros(DIMENSIONS, dtype=np.float64)
    for token, count in Counter(tokens).items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % DIMENSIONS
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign * (1.0 + math.log(count))
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def tokenize(text: str) -> list[str]:
    return [t for t in text.lower().split() if len(t) > 1]


@dataclass
class Corpus:
    texts: list[str]
    vectors: np.ndarray
    topic_of: list[str]
    identifier_of: list[str]


def build_corpus() -> Corpus:
    """A corpus where every chunk has one identifier and one topic.

    That structure is what makes a golden set possible without hand-labelling
    four thousand chunks: the query for a chunk is either its identifier or
    its topic's cue words, and the correct answer is known by construction.
    """
    rng = random.Random(SEED)
    texts, topics, identifiers = [], [], []
    topic_names = list(TOPICS)
    for index in range(CORPUS_SIZE):
        identifier = IDENTIFIERS[index % len(IDENTIFIERS)]
        topic = topic_names[index % len(topic_names)]
        words = [identifier, *rng.sample(TOPICS[topic], 3), *rng.sample(FILLER, 6)]
        rng.shuffle(words)
        texts.append(" ".join(words))
        topics.append(topic)
        identifiers.append(identifier)
    vectors = np.array([hashed_vector(tokenize(t)) for t in texts])
    return Corpus(texts, vectors, topics, identifiers)


def exact_search(corpus: Corpus, query: np.ndarray, limit: int = TOP_K) -> list[int]:
    """Every vector, every time. The answer other methods are scored against."""
    scores = corpus.vectors @ query
    return list(np.argsort(-scores)[:limit])


@dataclass
class IVF:
    """An inverted-file index: cluster the vectors, then probe some clusters.

    This is the structure behind most production vector indexes, FAISS's
    `IndexIVFFlat` included. HNSW reaches the same tradeoff by a different
    route, a navigable small-world graph instead of a partition, and the shape
    of its recall curve is the same: more work, more recall, diminishing
    returns.
    """

    centroids: np.ndarray
    members: list[np.ndarray]

    def search(self, corpus: Corpus, query: np.ndarray, nprobe: int, limit: int = TOP_K):
        order = np.argsort(-(self.centroids @ query))[:nprobe]
        candidates = np.concatenate([self.members[c] for c in order])
        if candidates.size == 0:
            return [], 0
        scores = corpus.vectors[candidates] @ query
        top = candidates[np.argsort(-scores)[:limit]]
        return list(top), int(candidates.size)


def build_ivf(corpus: Corpus, nlist: int = NLIST, rounds: int = 12) -> IVF:
    """Lloyd's algorithm, seeded, so the index is identical on every run."""
    rng = np.random.default_rng(SEED)
    centroids = corpus.vectors[rng.choice(len(corpus.vectors), nlist, replace=False)].copy()
    assignment = np.zeros(len(corpus.vectors), dtype=int)
    for _ in range(rounds):
        assignment = np.argmax(corpus.vectors @ centroids.T, axis=1)
        for cluster in range(nlist):
            members = corpus.vectors[assignment == cluster]
            if len(members):
                centroid = members.mean(axis=0)
                norm = np.linalg.norm(centroid)
                centroids[cluster] = centroid / norm if norm else centroid
    members = [np.flatnonzero(assignment == c) for c in range(nlist)]
    return IVF(centroids, members)


def recall_at_k(
    scores: np.ndarray, found: list[int], truth: list[int], tolerance: float = 1e-9
) -> float:
    """Recall at k, measured against the score boundary rather than the index set.

    The obvious implementation is `len(set(found) & set(truth)) / k`, and it is
    wrong whenever scores tie. This corpus ties constantly: distinct chunks
    with the same identifier and the same topic produce distinct vectors whose
    dot product with a given query is identical to the last bit, so the
    identity of the top ten is arbitrary among equals while the tenth-best
    score is not.

    That bug reported this index at 0.924 recall while probing every cluster,
    which is to say while doing exactly what exact search does. An index
    cannot lose recall against itself, so the number was measuring the
    measurement. Scoring against the k-th best score fixes it: an answer that
    is tied with a true answer is a true answer.
    """
    if not truth:
        return 1.0
    cutoff = scores[truth[-1]] - tolerance
    return sum(1 for item in found if scores[item] >= cutoff) / len(truth)


def timed(call, repeats: int) -> float:
    """Milliseconds per call, best of three batches.

    Best-of rather than mean, because this measures the index and the noise is
    all in one direction: another process on the machine can only slow a
    search down.
    """
    best = math.inf
    for _ in range(3):
        start = time.perf_counter()
        for _ in range(repeats):
            call()
        best = min(best, (time.perf_counter() - start) / repeats * 1000)
    return best


def part_one(corpus: Corpus, queries: list[np.ndarray]) -> dict[int, tuple[float, float, int]]:
    print("part 1: exact against approximate, on %d hashed vectors in %dd\n"
          % (CORPUS_SIZE, DIMENSIONS))

    index = build_ivf(corpus)
    sizes = [len(m) for m in index.members]
    print("  IVF: %d clusters, smallest %d, largest %d, mean %.0f vectors"
          % (NLIST, min(sizes), max(sizes), sum(sizes) / len(sizes)))

    truth = [exact_search(corpus, q) for q in queries]
    exact_ms = timed(lambda: exact_search(corpus, queries[0]), 20)
    print("  exact: %.2f ms per query, recall@%d 1.000 by definition\n"
          % (exact_ms, TOP_K))

    print("  nprobe  scanned  recall@%d  ms/query  speedup" % TOP_K)
    results = {}
    for nprobe in (1, 2, 4, 8, 16, 32, NLIST):
        recalls, scanned = [], 0
        for query, want in zip(queries, truth):
            found, seen = index.search(corpus, query, nprobe)
            recalls.append(recall_at_k(corpus.vectors @ query, found, want))
            scanned += seen
        recall = sum(recalls) / len(recalls)
        per_query = scanned // len(queries)
        ms = timed(lambda n=nprobe: index.search(corpus, queries[0], n), 20)
        results[nprobe] = (recall, ms, per_query)
        print("  %6d  %7d     %.3f  %8.2f  %5.1fx"
              % (nprobe, per_query, recall, ms, exact_ms / ms if ms else 0))

    good = [n for n, (r, _, _) in sorted(results.items()) if r >= 0.90]
    if good:
        recall, ms, scanned = results[good[0]]
        print(
            "\n  90%% recall first reached at nprobe=%d: %.3f recall for %.1fx the "
            "speed,\n  scanning %d of %d vectors. That is the knee, and the "
            "shape of this curve\n  is the whole reason an approximate index is "
            "worth operating."
            % (good[0], recall, exact_ms / ms if ms else 0, scanned, CORPUS_SIZE)
        )
    else:
        print("\n  no nprobe reached 90%% recall, which would make this index useless")
    return results


def part_two(corpus: Corpus) -> tuple[float, float, float]:
    """Try to show hybrid beating either half, and fail for an instructive reason.

    This was written to satisfy a backlog item asking for "a hybrid ranking
    beating either half". It does not, and the reason is the one thing the
    hashed-vector substitution cannot preserve.

    Hybrid search wins when the two retrievers fail on different queries.
    Lexical fails on paraphrase: a question with none of the chunk's words.
    Dense search answers those because an embedding model places related
    wordings near each other, having learned that they are related. A hash
    function has learned nothing. It places `cache` and `invalidate` in
    unrelated dimensions, exactly as it places `cache` and `banana`.

    So on this corpus the dense half has no query class of its own, and
    measuring it says so.
    """
    print("\n\npart 2: can hashed vectors show hybrid beating either half?\n")

    docs = [Counter(tokenize(text)) for text in corpus.texts]
    lengths = np.array([sum(d.values()) for d in docs], dtype=float)
    average = lengths.mean()
    frequency: Counter[str] = Counter()
    for doc in docs:
        frequency.update(doc.keys())
    total = len(docs)
    idf = {t: math.log(1 + (total - c + 0.5) / (c + 0.5)) for t, c in frequency.items()}
    k1, b = 1.2, 0.75

    def lexical(query: str, limit: int = TOP_K) -> list[int]:
        terms = tokenize(query)
        scores = np.zeros(total)
        for position, (doc, length) in enumerate(zip(docs, lengths)):
            score = 0.0
            for term in terms:
                count = doc.get(term, 0)
                if not count:
                    continue
                norm = 1 - b + b * (length / average)
                score += idf.get(term, 0.0) * (count * (k1 + 1)) / (count + k1 * norm)
            scores[position] = score
        return [int(i) for i in np.argsort(-scores)[:limit] if scores[i] > 0]

    index = build_ivf(corpus)

    def dense(query: str, limit: int = TOP_K) -> list[int]:
        found, _ = index.search(corpus, hashed_vector(tokenize(query)), 8, limit)
        return [int(i) for i in found]

    def rrf(*rankings: list[int]) -> list[int]:
        scores: dict[int, float] = {}
        for ranking in rankings:
            for rank, item in enumerate(ranking, start=1):
                scores[item] = scores.get(item, 0.0) + 1.0 / (RRF_K + rank)
        return sorted(scores, key=lambda i: -scores[i])

    # Relevance is judged by class, not by a single chunk. Eighty-two chunks
    # carry `batch_size`, so "which one did I mean" is not a question any
    # retriever could answer; "did it return chunks about batch_size" is.
    rng = random.Random(SEED + 1)
    cases: list[tuple[str, str, str]] = []
    for position, target in enumerate(rng.sample(range(CORPUS_SIZE), 40)):
        if position % 2 == 0:
            cases.append((corpus.identifier_of[target], "identifier", corpus.identifier_of[target]))
        else:
            topic = corpus.topic_of[target]
            # A paraphrase: the topic named in words the chunks do not use.
            paraphrase = {
                "latency": "requests are taking too long to come back",
                "throughput": "how many things can it get through per second",
                "memory": "it is using too much ram on the box",
                "caching": "stop it reusing the previous answer",
                "errors": "it stopped and printed a number",
                "config": "where do i change the setting",
            }[topic]
            cases.append((paraphrase, "topic", topic))

    def correct(position: int, kind: str, label: str) -> bool:
        if kind == "identifier":
            return corpus.identifier_of[position] == label
        return corpus.topic_of[position] == label

    precision: dict[str, dict[str, list[float]]] = {
        name: {"identifier": [], "topic": []} for name in ("lexical", "dense", "hybrid")
    }
    for query, kind, label in cases:
        rankings = {"lexical": lexical(query), "dense": dense(query)}
        rankings["hybrid"] = rrf(rankings["lexical"], rankings["dense"])
        for name, ranking in rankings.items():
            top = ranking[:TOP_K]
            hits = sum(1 for position in top if correct(position, kind, label))
            precision[name][kind].append(hits / TOP_K)

    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    print("  %-10s %-14s %-14s %s" % ("retriever", "identifier", "paraphrase", "both"))
    overall = {}
    for name in ("lexical", "dense", "hybrid"):
        identifier = mean(precision[name]["identifier"])
        topic = mean(precision[name]["topic"])
        overall[name] = (identifier + topic) / 2
        print(
            "  %-10s %-14s %-14s %.3f"
            % (name, f"{identifier:.3f}", f"{topic:.3f}", overall[name])
        )

    print(
        "\n  precision@%d, half the queries naming an identifier and half "
        "paraphrasing a\n  topic in words no chunk uses."
        % TOP_K
    )
    print(
        "\n  Read the paraphrase column first. Lexical scores 0.1 and dense "
        "scores zero,\n  so neither half answers the query class that hybrid "
        "search exists for, and\n  fusing two retrievers that both fail "
        "produces a third that also fails.\n"
        "\n  Then read the identifier column, which is the actual finding. "
        "Dense scores\n  0.88 there, nearly as well as BM25. A dense "
        "retriever is not supposed to be\n  good at exact identifiers; that "
        "is the failure the whole page is about. It\n  scores well here "
        "because feature hashing sends one token to one dimension,\n  so a "
        "query of one identifier is a near-one-hot vector and the search is "
        "a\n  lexical lookup wearing vector clothes.\n"
        "\n  That is the honest boundary of a dependency-free "
        "demonstration, and it cuts\n  cleanly. Part 1 is a real "
        "measurement of a real index: recall and latency are\n  properties "
        "of the geometry and do not care where the vectors came from.\n  "
        "Retrieval quality is a property of the representation, so hashed "
        "vectors can\n  say nothing about it. The hybrid argument belongs "
        "to the `vector-stores`\n  page's own cue-based stand-in, which at "
        "least has a topic space, and a real\n  quality claim needs a real "
        "model."
    )
    return overall["lexical"], overall["dense"], overall["hybrid"]


def main() -> int:
    corpus = build_corpus()
    rng = random.Random(SEED + 2)
    queries = [
        hashed_vector(tokenize(corpus.texts[i]))
        for i in rng.sample(range(CORPUS_SIZE), 25)
    ]

    results = part_one(corpus, queries)
    lexical, dense, hybrid = part_two(corpus)

    print(
        "\n\nThe two parts answer different questions, and only one of them "
        "can be\nanswered without a model. Part 1 is about the store: what an "
        "approximate index\ncosts in recall and buys in latency, which is a "
        "fact about clustering points.\nPart 2 is about retrieval design, "
        "which is a fact about meaning, and a hash\nfunction does not have "
        "any.\n\nThe useful thing to carry from part 1 is the shape rather "
        "than the numbers:\nrecall climbs steeply and then flattens, and past "
        "the flattening the\napproximate index is slower than scanning "
        "everything, because gathering\ncandidates costs more than the "
        "comparisons it saves. A vector store tuned past\nits own knee is "
        "doing more work than brute force for the same answer."
    )

    # Part 1's two claims are assertions about the index. Part 2's is an
    # assertion about the substitution's limit, which is the finding: if
    # hashed vectors ever did beat lexical retrieval on paraphrase, the
    # explanation in part 2 would be wrong and this should fail.
    full_recall = results[NLIST][0]
    ok = (
        math.isclose(full_recall, 1.0, abs_tol=1e-9)
        and results[1][0] < 0.7
        and lexical > dense
    )
    if not ok:
        print(
            "unexpected: probing every cluster should recover exact recall "
            "exactly, probing one cluster should lose most of it, and hashed "
            f"vectors should not beat lexical search (got {results[1][0]:.3f}, "
            f"{full_recall:.3f}, {dense:.3f} against {lexical:.3f})",
            file=sys.stderr,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

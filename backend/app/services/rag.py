import json
import math
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import httpx

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None  # type: ignore

from app.schemas import Source

TOKEN_PATTERN = re.compile(r"[a-z0-9']+")
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "ifab_laws_seed.json"
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "their",
    "to",
    "when",
    "with",
}

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if openai is not None and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_API_BASE_URL = os.getenv("NVIDIA_API_BASE_URL", "https://api.nvidia.ai")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL")
NVIDIA_EMBEDDING_MODEL = os.getenv("NVIDIA_EMBEDDING_MODEL")


@dataclass(frozen=True)
class LawChunk:
    id: str
    law: str
    title: str
    url: str
    scenario_type: str
    text: str


@dataclass(frozen=True)
class RetrievalResult:
    chunk: LawChunk
    score: float


@lru_cache
def load_law_chunks() -> list[LawChunk]:
    with DATA_PATH.open() as data_file:
        rows = json.load(data_file)
    return [LawChunk(**row) for row in rows]


def _openai_enabled() -> bool:
    return LLM_PROVIDER == "openai" and openai is not None and bool(OPENAI_API_KEY)


def _nvidia_enabled() -> bool:
    return LLM_PROVIDER == "nvidia" and bool(NVIDIA_API_KEY) and bool(NVIDIA_MODEL)


def retrieve_laws(question: str, limit: int = 3) -> list[RetrievalResult]:
    if _openai_enabled():
        try:
            return retrieve_laws_with_openai_embeddings(question, limit)
        except Exception:
            return retrieve_laws_bm25(question, limit)

    if _nvidia_enabled():
        try:
            return retrieve_laws_with_nvidia_embeddings(question, limit)
        except Exception:
            return retrieve_laws_bm25(question, limit)

    return retrieve_laws_bm25(question, limit)


def retrieve_laws_bm25(question: str, limit: int = 3) -> list[RetrievalResult]:
    chunks = load_law_chunks()
    query_tokens = _tokenize(question)
    if not query_tokens:
        return []

    document_tokens = [_tokenize(f"{chunk.law} {chunk.title} {chunk.text}") for chunk in chunks]
    document_frequency = {
        token: sum(1 for tokens in document_tokens if token in tokens) for token in set().union(*document_tokens)
    }

    results: list[RetrievalResult] = []
    for chunk, tokens in zip(chunks, document_tokens):
        score = _bm25_score(query_tokens, tokens, document_frequency, len(chunks))
        if score > 0:
            results.append(RetrievalResult(chunk=chunk, score=round(score, 3)))

    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]


def retrieve_laws_with_openai_embeddings(question: str, limit: int = 3) -> list[RetrievalResult]:
    chunks = load_law_chunks()
    query_embedding = _openai_embedding(question)
    if query_embedding is None:
        return retrieve_laws_bm25(question, limit)

    chunk_embeddings = load_chunk_embeddings(chunks)
    results = [
        RetrievalResult(chunk=chunk, score=round(_cosine_similarity(query_embedding, embedding), 6))
        for chunk, embedding in zip(chunks, chunk_embeddings)
    ]
    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]


def retrieve_laws_with_nvidia_embeddings(question: str, limit: int = 3) -> list[RetrievalResult]:
    chunks = load_law_chunks()
    query_embedding = _nvidia_embedding(question)
    if query_embedding is None:
        return retrieve_laws_bm25(question, limit)

    chunk_embeddings = load_chunk_embeddings(chunks)
    results = [
        RetrievalResult(chunk=chunk, score=round(_cosine_similarity(query_embedding, embedding), 6))
        for chunk, embedding in zip(chunks, chunk_embeddings)
    ]
    return sorted(results, key=lambda result: result.score, reverse=True)[:limit]


def load_chunk_embeddings(chunks: list[LawChunk]) -> list[list[float]]:
    cache_path = _embedding_cache_path()
    if cache_path.exists():
        cached_embeddings = json.loads(cache_path.read_text())
        if len(cached_embeddings) == len(chunks):
            return cached_embeddings

    embeddings = [
        _provider_embedding(f"{chunk.law} {chunk.title} {chunk.text}") or []
        for chunk in chunks
    ]
    cache_path.write_text(json.dumps(embeddings))
    return embeddings


def _embedding_cache_path() -> Path:
    model_tag = OPENAI_EMBEDDING_MODEL if _openai_enabled() else NVIDIA_EMBEDDING_MODEL or NVIDIA_MODEL or "default"
    return Path(__file__).resolve().parents[1] / "data" / f"ifab_laws_embeddings_{LLM_PROVIDER}_{model_tag}.json"


def _provider_embedding(text: str) -> list[float] | None:
    if _openai_enabled():
        return _openai_embedding(text)
    if _nvidia_enabled():
        return _nvidia_embedding(text)
    return None


def _openai_embedding(text: str) -> list[float] | None:
    if not _openai_enabled():
        return None

    response = openai.Embedding.create(model=OPENAI_EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def _nvidia_embedding(text: str) -> list[float] | None:
    if not _nvidia_enabled():
        return None

    embedding_model = NVIDIA_EMBEDDING_MODEL or NVIDIA_MODEL
    url = f"{NVIDIA_API_BASE_URL.rstrip('/')}/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }
    response = httpx.post(url, headers=headers, json={"model": embedding_model, "input": text}, timeout=30)
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def build_grounded_answer(question: str, results: list[RetrievalResult]) -> str:
    if not results:
        return (
            "I could not find a strong match in the local IFAB law seed yet. "
            "Try asking about offside, penalties, fouls, throw-ins, cards, or when the ball is out of play."
        )

    if _openai_enabled():
        try:
            return _generate_openai_answer(question, results)
        except Exception:
            pass

    if _nvidia_enabled():
        try:
            return _generate_nvidia_answer(question, results)
        except Exception:
            pass

    primary = results[0].chunk
    evidence = " ".join(result.chunk.text for result in results[:2])
    return (
        f"Based on {primary.law}, {primary.title.lower()}: {evidence} "
        "In beginner terms, focus on the trigger, the location, and the restart. "
        "That combination usually explains why the referee gives this decision."
    )


def _generate_openai_answer(question: str, results: list[RetrievalResult]) -> str:
    retrieved_context = "\n\n".join(
        f"{result.chunk.law} {result.chunk.title}: {result.chunk.text}" for result in results
    )
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a friendly football rules coach for a first-time fan. "
                "Answer clearly and concisely using only the retrieved IFAB law excerpts provided. "
                "If the question cannot be answered from the retrieved rules, say that the information is not available."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                "Retrieved law excerpts:\n"
                f"{retrieved_context}\n\n"
                "Use the law titles when explaining the rule, and keep the answer beginner-friendly."
            ),
        },
    ]

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=prompt,
        temperature=0.2,
        max_tokens=450,
    )
    return response.choices[0].message["content"].strip()


def _generate_nvidia_answer(question: str, results: list[RetrievalResult]) -> str:
    retrieved_context = "\n\n".join(
        f"{result.chunk.law} {result.chunk.title}: {result.chunk.text}" for result in results
    )
    url = f"{NVIDIA_API_BASE_URL.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a friendly football rules coach for a first-time fan. "
                    "Answer clearly and concisely using only the retrieved IFAB law excerpts provided. "
                    "If the question cannot be answered from the retrieved rules, say that the information is not available."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    "Retrieved law excerpts:\n"
                    f"{retrieved_context}\n\n"
                    "Use the law titles when explaining the rule, and keep the answer beginner-friendly."
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 450,
    }
    response = httpx.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def sources_from_results(results: list[RetrievalResult]) -> list[Source]:
    return [
        Source(
            title=f"{result.chunk.law}: {result.chunk.title}",
            detail=result.chunk.text,
            url=result.chunk.url,
            score=result.score,
        )
        for result in results
    ]


def scenario_from_results(results: list[RetrievalResult]) -> str:
    for result in results:
        if result.chunk.scenario_type != "general":
            return result.chunk.scenario_type
    return "general"


def _tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOP_WORDS]


def _cosine_similarity(first: list[float], second: list[float]) -> float:
    dot = sum(a * b for a, b in zip(first, second))
    norm_a = math.sqrt(sum(a * a for a in first))
    norm_b = math.sqrt(sum(b * b for b in second))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _bm25_score(
    query_tokens: list[str],
    document_tokens: list[str],
    document_frequency: dict[str, int],
    document_count: int,
) -> float:
    score = 0.0
    length = len(document_tokens) or 1
    average_length = 55
    k1 = 1.5
    b = 0.75

    for token in query_tokens:
        term_frequency = document_tokens.count(token)
        if not term_frequency:
            continue
        idf = math.log(1 + (document_count - document_frequency[token] + 0.5) / (document_frequency[token] + 0.5))
        numerator = term_frequency * (k1 + 1)
        denominator = term_frequency + k1 * (1 - b + b * length / average_length)
        score += idf * numerator / denominator
    return score

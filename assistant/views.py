import json
from typing import List, Dict, Any

from django.db.models import Q
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import spacy
from courses.models import Course
from typing import Tuple
import math

MIN_K = 4                  # always retrieve at least this many (if available)
MAX_FETCH = 24             # candidate pool size to consider per query
TOKEN_BUDGET = 1500        # approx tokens you allow for the context
TOKENS_PER_CHAR = 0.25     # rough heuristic: 4 chars ≈ 1 token

def est_tokens(text: str) -> int:
    # super light heuristic; good enough for budgeting
    return int(len(text) * TOKENS_PER_CHAR) + 1

def combined_rank_score(doc, base_score: float, query_ents) -> float:
    # base_score: vector relevance (0..1 usually; if unknown, assume 0.5)
    ents = set(map(str, doc.metadata.get("entities", [])))
    overlap = len(ents.intersection(set(query_ents)))
    # Weighting: tune alpha/beta to your liking
    alpha = 0.7  # vector similarity
    beta  = 0.3  # KG entity overlap
    # Normalize overlap a bit (log to avoid huge jumps)
    overlap_signal = math.log1p(overlap) / math.log(1 + 8)  # cap ~8 ents
    return alpha * base_score + beta * overlap_signal

_NLP = None
def nlp():
    global _NLP
    if _NLP is None:
        _NLP = spacy.load("en_core_web_sm")
    return _NLP

def _embedding():
    return OllamaEmbeddings(model=getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text"))

def _llm():
    return Ollama(model=getattr(settings, "OLLAMA_LLM_MODEL", "llama3"), temperature=0.1)

def extract_query_entities(q: str) -> List[str]:
    doc = nlp()(q)
    ents = {e.text for e in doc.ents}
    ents |= {t.lemma_ for t in doc if t.pos_ in {"NOUN","PROPN"} and len(t) > 2}
    return list(ents)

def kg_rerank(query_ents: List[str], docs: List[Document]) -> List[Document]:
    # Simple boost: sort by overlap count with chunk entities metadata
    def overlap(d: Document) -> int:
        ents = set(map(str, d.metadata.get("entities", [])))
        return len(ents.intersection(set(query_ents)))
    return sorted(docs, key=overlap, reverse=True)

PROMPT = PromptTemplate.from_template(
    """You are a helpful teaching assistant. Answer the question ONLY using the provided context.
If you are unsure, say you don't know.
After your answer, include a short "Sources:" list with (Material Title — p. X) for each cited chunk.

Question: {question}

Context:
{context}

Answer:"""
)

def format_context(docs: List[Document]) -> str:
    blocks = []
    for d in docs:
        title = d.metadata.get("material_title", "Unknown")
        page = d.metadata.get("page", "?")
        blocks.append(f"[{title} — p.{page}]\n{d.page_content}")
    return "\n\n---\n\n".join(blocks)

def build_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for d in docs:
        key = (d.metadata.get("material_title"), d.metadata.get("page"))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "material_title": d.metadata.get("material_title"),
            "page": d.metadata.get("page"),
            "material_id": d.metadata.get("material_id"),
        })
    return out

@csrf_exempt
@require_POST
def response(request: HttpRequest):
    data = json.loads(request.body.decode("utf-8"))
    course_id = str(data["course_id"])
    question = data["question"]

    db = Chroma(
        persist_directory=str(settings.AI_DB_DIR / course_id),
        embedding_function=_embedding()
    )

    # Treat provided k as an upper bound (cap)
    k_cap = int(data.get("k", 0)) or None

    # 2) Retrieve a larger candidate pool with scores
    q_ents = extract_query_entities(question)

    docs_with_scores: list[Tuple[Document, float]] = []
    try:
        # Best: get relevance scores directly (0..1 typically)
        results = db.similarity_search_with_relevance_scores(
            question, k=MAX_FETCH, filter={"course_id": course_id}
        )
        # results is list[(Document, score)]
        docs_with_scores = results
    except Exception:
        # Fallback: use retriever (no scores)
        retriever = db.as_retriever(search_kwargs={
            "k": MAX_FETCH,
            "filter": {"course_id": course_id}
        })
        base_docs: List[Document] = retriever.get_relevant_documents(question)
        # Assume a neutral base score if not provided
        docs_with_scores = [(d, 0.5) for d in base_docs]

    # 3) Re-rank by combined score (vector score + KG overlap)
    ranked = sorted(
        docs_with_scores,
        key=lambda t: combined_rank_score(t[0], t[1], q_ents),
        reverse=True
    )

    # 4) Trim to token budget (while keeping >= MIN_K)
    selected_docs: List[Document] = []
    used_tokens = 0
    min_keep = MIN_K

    for doc, _score in ranked:
        chunk_tokens = est_tokens(doc.page_content)
        # If we haven't reached min_keep, we always take it (if available)
        if len(selected_docs) < min_keep:
            selected_docs.append(doc)
            used_tokens += chunk_tokens
            continue

        # After min_keep, respect the token budget
        if used_tokens + chunk_tokens > TOKEN_BUDGET:
            break
        selected_docs.append(doc)
        used_tokens += chunk_tokens

    # Optional: cap by user-provided k (if any)
    if k_cap is not None and len(selected_docs) > k_cap:
        selected_docs = selected_docs[:k_cap]

    # Safety: if nothing selected but we had candidates, keep the top few
    if not selected_docs and ranked:
        selected_docs = [d for d, _ in ranked[:min_keep]]

    # 5) Compose and call LLM
    context = format_context(selected_docs)
    prompt = PROMPT.format(question=question, context=context)
    llm = _llm()
    answer = llm.invoke(prompt)

    return JsonResponse({
        "answer": answer.strip(),
        "sources": build_sources(selected_docs),
        "used_entities": q_ents,
    })


def chat_page(request):
    user = request.user
    courses = Course.objects.filter(
        Q(instructor__user=user) |
        Q(teaching_assistants__user=user) |
        Q(enrollment__student__user=user)
    ).distinct().order_by("name")

    context = {
        "courses": courses,
    }
    return render(request, "assistant/chat.html", context=context)

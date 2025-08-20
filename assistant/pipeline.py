import json
import os
from pathlib import Path
from typing import List, Dict, Tuple

import fitz
import networkx as nx
import spacy
from django.conf import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

_NLP = None
def nlp():
    global _NLP
    if _NLP is None:
        _NLP = spacy.load("en_core_web_sm")
    return _NLP

def _material_dir(course_id: int, material_id: int) -> Path:
    base = Path(settings.AI_DB_DIR) / str(course_id) / str(material_id)
    base.mkdir(parents=True, exist_ok=True)
    return base

def extract_text_per_page(pdf_path: str) -> List[Tuple[int, str]]:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc, start=1):
        pages.append((i, page.get_text()))
    return pages

def chunk_pages(pages: List[Tuple[int, str]]) -> List[Dict]:
    # Chunk by ~1200 chars with 200 overlap to support large PDFs
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for page_num, text in pages:
        for chunk in splitter.split_text(text):
            chunks.append({"page": page_num, "text": chunk})
    return chunks

def extract_entities(text: str) -> List[str]:
    doc = nlp()(text)
    # Keep common academic NER types + nouns (simple boost)
    ents = {ent.text.strip() for ent in doc.ents if ent.label_ in {
        "PERSON","ORG","GPE","LOC","PRODUCT","EVENT","WORK_OF_ART","NORP"
    }}
    # Add top nouns as lightweight concepts
    ents |= {t.lemma_ for t in doc if t.pos_ in {"NOUN","PROPN"} and len(t) > 2}
    # Clean / dedupe
    cleaned = sorted({e for e in ents if any(c.isalnum() for c in e)})
    return cleaned

def build_light_kg(chunks: List[Dict]) -> Tuple[nx.Graph, Dict[str, List[int]]]:
    """Build a simple co-occurrence knowledge graph:
    - Nodes: entities
    - Edge: entities that co-occur within the same chunk
    Return (graph, entity->chunk_ids index).
    """
    G = nx.Graph()
    index: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        ents = extract_entities(c["text"])
        for e in ents:
            index.setdefault(e, []).append(idx)
            if not G.has_node(e):
                G.add_node(e)
        # Co-occurrence edges
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                u, v = ents[i], ents[j]
                if G.has_edge(u, v):
                    G[u][v]["weight"] += 1
                else:
                    G.add_edge(u, v, weight=1)
        c["entities"] = ents  # store on chunk for later filtering/boosting
    return G, index

def _embedding():
    return OllamaEmbeddings(model=getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text"))

def upsert_chroma(course_id: int, material_id: int, material_title: str, chunks: List[Dict], persist_dir: str):
    embed = _embedding()
    # One Chroma per course to allow cross-material retrieval, but we store rich metadata
    course_dir = Path(persist_dir) / str(course_id)
    course_dir.mkdir(parents=True, exist_ok=True)
    db = Chroma(persist_directory=str(course_dir), embedding_function=embed)

    texts = [c["text"] for c in chunks]
    metadatas = [{
        "course_id": str(course_id),
        "material_id": str(material_id),
        "material_title": material_title,
        "page": c["page"],
        "entities": c.get("entities", []),
    } for c in chunks]

    # IDs ensure idempotent-ish adds per material; include material and local index
    ids = [f"m{material_id}_c{i}" for i in range(len(chunks))]
    db.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    db.persist()

def process_material(material) -> None:
    """
    Orchestrates: PDF -> pages -> chunks -> entities -> KG -> Chroma upsert.
    Saves:
      - GraphML at db/courses/<course>/<material>/graph.graphml
      - Entity->chunks map at .../entity_index.json
    """
    course_id = material.course.id
    material_id = material.id
    title = material.title
    pdf_path = material.upload.path

    # 1) Extract and chunk
    pages = extract_text_per_page(pdf_path)
    chunks = chunk_pages(pages)

    # 2) Build light knowledge graph + entity index
    G, entity_index = build_light_kg(chunks)
    mdir = _material_dir(course_id, material_id)
    nx.write_graphml(G, mdir / "graph.graphml")
    with open(mdir / "entity_index.json", "w", encoding="utf-8") as f:
        json.dump(entity_index, f, ensure_ascii=False, indent=2)

    # 3) Upsert into per-course Chroma vectorstore with metadata
    upsert_chroma(course_id, material_id, title, chunks, persist_dir=str(settings.AI_DB_DIR))

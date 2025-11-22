"""Controllers: FastAPI route handlers separated from app setup.
"""
from __future__ import annotations

import logging
import os
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import services

logger = logging.getLogger("fragaz.controllers")

router = APIRouter()


class QueryRequest(BaseModel):
    q: str
    k: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    confidence: dict
    sources: List[dict]


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    try:
        logger.info("/query recebido: %s", req.q[:120])
        sources = services.retrieve_docs(req.q, k=req.k or 5)
        rs = 0.0
        if sources:
            vals = [s.get("score") for s in sources if isinstance(s.get("score"), (int, float))]
            rs = float(sum(vals) / len(vals)) if vals else 0.0

        # Simple answer generation (can be extended to use genai)
        answer = "".join([s.get("content", "")[:500] for s in sources[:3]]) or "Sem resposta."
        confidence = {"Rs": rs, "note": "Rs = média simples dos scores recuperados (0..1)"}
        resp = {"answer": answer, "confidence": confidence, "sources": sources}
        logger.info("Resposta gerada (chars=%d) - Rs=%.3f", len(answer), rs)
        return resp
    except Exception as e:
        logger.exception("Erro no endpoint /query: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class ScrapeConfluenceRequest(BaseModel):
    url: str
    collection_name: Optional[str] = None
    username: Optional[str] = None
    api_token: Optional[str] = None
    title: Optional[str] = None


@router.post("/scrape/confluence")
def scrape_confluence(req: ScrapeConfluenceRequest):
    try:
        logger.info("/scrape/confluence solicitado: %s", req.url)
        # Use the logic from services but keep controller thin
        import requests
        from bs4 import BeautifulSoup
        from sentence_transformers import SentenceTransformer

        headers = {"User-Agent": "FRAGAZ-Scraper/1.0"}
        auth = None
        if req.username and req.api_token:
            from requests.auth import HTTPBasicAuth

            auth = HTTPBasicAuth(req.username, req.api_token)

        r = requests.get(req.url, headers=headers, auth=auth, timeout=30)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Falha ao buscar página Confluence: {r.status_code}")

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n")

        max_len = 800
        chunks: List[str] = []
        for para in text.splitlines():
            p = para.strip()
            if not p:
                continue
            while len(p) > max_len:
                chunks.append(p[:max_len])
                p = p[max_len:]
            chunks.append(p)

        if not chunks:
            raise HTTPException(status_code=400, detail="Nenhum conteúdo extraído da página.")

        emb_model = None
        try:
            emb_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        except Exception:
            emb_model = None

        embedding_vectors = []
        if emb_model:
            for c in chunks:
                embedding_vectors.append(emb_model.encode([c])[0].tolist())
        else:
            for c in chunks:
                embedding_vectors.append(services._embed_text(c, dim=128))

        collection_name = req.collection_name or os.environ.get("COLLECTION_NAME", "fragaz")
        ids = [f"confluence-{int(time.time())}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": req.url, "title": req.title or req.url, "chunk_index": i} for i in range(len(chunks))]

        services.add_documents_to_chroma(collection_name, chunks, metadatas, ids, embeddings=embedding_vectors)
        logger.info("Adicionados %d chunks ao Chroma collection=%s", len(chunks), collection_name)
        return {"status": "success", "added": len(chunks), "collection": collection_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro em /scrape/confluence: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

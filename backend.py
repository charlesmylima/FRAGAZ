"""Backend FastAPI para FRAGAZ

Funcionalidades:
- FastAPI app com POST /query
- Tenta usar ChromaDB (HttpClient ou local persist) para recuperação
- Tenta usar Google GenAI (`genai`) quando `GEMINI_API_KEY`/`GOOGLE_API_KEY` estiver setada
- Fallback para busca local usando `.fragaz_index.json` e embeddings determinísticos
- Logs claros para operações e erros (console + rotating file)
- Pode ser executado com auto-reload: `python backend.py` (usa uvicorn.run with reload=True)

Crie um venv e instale dependências se necessário (FastAPI, uvicorn, chromadb, genai, numpy, langchain_community).
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
import requests
import time

try:
    import numpy as np
except Exception:
    np = None  # type: ignore

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Optional heavy libraries are imported lazily to keep startup fast.
# They will only be attempted when explicitly enabled via environment
# variables such as `ENABLE_CHROMA=1` or when a GEMINI/GOOGLE key is present.
chromadb = None
Settings = None
CHROMA_AVAILABLE = False
genai = None
GENAI_AVAILABLE = False
HuggingFaceEmbeddings = None
LANGCHAIN_HF = False

# Paths
ROOT = Path(__file__).resolve().parent
INDEX_FILE = ROOT / ".fragaz_index.json"
CHROMA_DIR = ROOT / ".chromadb_fragaz"

# Hardcode Gemini API key fallback if not provided via env (user requested)
# WARNING: this embeds a secret into the source. Prefer env vars in real deployments.
_GEMINI_FALLBACK = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not _GEMINI_FALLBACK:
    # user-provided key (hardcoded per request)
    _GEMINI_FALLBACK = "AIzaSyBd8QXKbgHYvdTIg1vQeZDAONpvEtdEKwk"
    os.environ["GEMINI_API_KEY"] = _GEMINI_FALLBACK
    # logger is configured further below; print a clear message for early visibility
    print("WARNING: GEMINI_API_KEY não definido. Usando chave hard-coded por solicitação (não recomendado em produção).")

# Logging setup
LOG_FILE = ROOT / "backend.log"
logger = logging.getLogger("fragaz.backend")
logger.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(fmt)
logger.addHandler(ch)
try:
    from logging.handlers import RotatingFileHandler

    fh = RotatingFileHandler(str(LOG_FILE), maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
except Exception:
    logger.warning("RotatingFileHandler não disponível — logs em arquivo desabilitados")

# Hardcoded API key (per user request). This will be used only if no
# `GEMINI_API_KEY` or `GOOGLE_API_KEY` env var is present. WARNING: hardcoding
# secrets in source is insecure; remove the literal before sharing the repo.
# Set to empty string to disable.
HARDCODED_GEMINI_KEY = "AIzaSyBd8QXKbgHYvdTIg1vQeZDAONpvEtdEKwk"
if HARDCODED_GEMINI_KEY and not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
    os.environ["GEMINI_API_KEY"] = HARDCODED_GEMINI_KEY
    logger.warning("ATENÇÃO: Usando GEMINI_API_KEY hardcoded em `backend.py`. Remova essa chave antes de comitar/compartilhar`.")

# Defaults for Chroma remote (user requested hard-coded IP)
os.environ.setdefault("CHROMA_SERVER_IP", os.environ.get("CHROMA_SERVER_IP") or "134.65.230.237")
os.environ.setdefault("CHROMA_SERVER_PORT", os.environ.get("CHROMA_SERVER_PORT") or "8000")
os.environ.setdefault("CHROMA_AUTH_TOKEN", os.environ.get("CHROMA_AUTH_TOKEN") or "StocksRAG")

# Defaults for OCI (can be overridden via env vars)
os.environ.setdefault("OCI_NAMESPACE", os.environ.get("OCI_NAMESPACE") or "axnosoetk7zq")
os.environ.setdefault("OCI_BUCKET_NAME", os.environ.get("OCI_BUCKET_NAME") or "bucket-20251017-0832")


@dataclass
class IndexEntry:
    id: str
    title: str
    content: str
    source: str
    embedding: List[float]


def _embed_text(text: str, dim: int = 128) -> List[float]:
    """Fallback deterministic embedding (sha256 based)."""
    import hashlib

    h = hashlib.sha256(text.encode("utf-8")).digest()
    rep = (dim + len(h) - 1) // len(h)
    buf = (h * rep)[:dim]
    vals = [((b / 255.0) * 2.0 - 1.0) for b in buf]
    return vals


def _cosine_sim(a: List[float], b: List[float]) -> float:
    if np is not None:
        va = np.array(a, dtype=float)
        vb = np.array(b, dtype=float)
        denom = (np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)
    # pure python fallback
    dot = sum(x * y for x, y in zip(a, b))
    lena = sum(x * x for x in a) ** 0.5
    lenb = sum(x * x for x in b) ** 0.5
    if lena * lenb == 0:
        return 0.0
    return dot / (lena * lenb)


def load_index() -> List[IndexEntry]:
    if not INDEX_FILE.exists():
        logger.info("Índice local não encontrado: %s", INDEX_FILE)
        return []
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        return [IndexEntry(**d) for d in data]
    except Exception as e:
        logger.error("Falha ao carregar índice local: %s", e)
        return []


def retrieve_docs(query: str, k: int = 5) -> List[Dict]:
    """Tenta recuperar do Chroma se disponível, senão do índice local."""
    logger.info("Recuperando top %d docs para query: %s", k, query[:80])
    results = []

    # Try Chroma remote (HTTP) if environment configured or explicitly enabled
    chroma_host = os.environ.get("CHROMA_SERVER_IP")
    chroma_port = os.environ.get("CHROMA_SERVER_PORT")
    chroma_token = os.environ.get("CHROMA_AUTH_TOKEN")
    enable_chroma_env = os.environ.get("ENABLE_CHROMA", "0") == "1"
    enable_chroma = enable_chroma_env or (chroma_host and chroma_port)

    if enable_chroma:
        try:
            # import chromadb lazily to avoid heavy startup costs when unused
            import chromadb as _chromadb
            try:
                from chromadb.config import Settings as _Settings
            except Exception:
                _Settings = None

            # prefer HTTP client if host/port present
            if chroma_host and chroma_port:
                logger.info("Usando Chroma HTTP client %s:%s", chroma_host, chroma_port)
                try:
                    client = _chromadb.HttpClient(host=chroma_host, port=int(chroma_port), headers={"X-Chroma-Token": chroma_token} if chroma_token else None)
                except Exception:
                    if _Settings is not None:
                        client = _chromadb.Client(_Settings(persist_directory=str(CHROMA_DIR)))
                    else:
                        client = _chromadb.Client()
            else:
                if _Settings is not None:
                    client = _chromadb.Client(_Settings(persist_directory=str(CHROMA_DIR)))
                else:
                    client = _chromadb.Client()

            collection_name = os.environ.get("COLLECTION_NAME", "fragaz")
            coll = client.get_collection(collection_name)
            res = coll.query(query_texts=[query], n_results=k, include=["documents", "metadatas", "ids", "distances"])  # type: ignore
            ids = res.get("ids", [[]])[0]
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            dists = res.get("distances", [[]])[0]
            for _id, doc, meta, dist in zip(ids, docs, metas, dists):
                results.append({
                    "id": _id,
                    "title": meta.get("title") if isinstance(meta, dict) else None,
                    "content": doc,
                    "source": meta.get("source") if isinstance(meta, dict) else None,
                    "score": float(max(0.0, 1.0 - dist)) if isinstance(dist, (int, float)) else None,
                })
            if results:
                logger.info("Recuperado %d docs de Chroma", len(results))
                return results
        except Exception as e:
            logger.exception("Chroma falhou: %s", e)

    # fallback local search
    entries = load_index()
    if not entries:
        logger.info("Nenhum documento local para recuperar.")
        return []
    qv = _embed_text(query, dim=len(entries[0].embedding) if entries and entries[0].embedding else 128)
    scored = [(e, _cosine_sim(qv, e.embedding)) for e in entries]
    scored.sort(key=lambda t: t[1], reverse=True)
    for e, sc in scored[:k]:
        results.append({
            "id": e.id,
            "title": e.title,
            "content": e.content,
            "source": e.source,
            "score": float(sc),
        })
    logger.info("Recuperado %d docs do índice local", len(results))
    return results


def generate_answer_from_context(query: str, sources: List[Dict]) -> str:
    """Tenta gerar resposta com genai; senão fallback concatenação."""
    if not sources:
        return "Não foi possível recuperar contexto relevante para responder à pergunta."

    try:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        enable_genai = os.environ.get("ENABLE_GENAI", "1") != "0"
        if api_key and enable_genai:
            try:
                import genai as _genai
                logger.info("Usando genai para gerar resposta (modelo: %s)", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
                _genai.configure(api_key=api_key)
                model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
                model = _genai.GenerativeModel(model_name)
                ctx = "\n\n---\n\n".join([s["content"][:1500] for s in sources])
                prompt = f"Contexto:\n{ctx}\n\nPergunta: {query}\n\nResponda de forma objetiva e fundamente suas afirmações citando as fontes quando possível."  # noqa: E501
                resp = model.generate_content(prompt)
                text = getattr(resp, "text", None) or str(resp)
                return text.strip()
            except Exception:
                logger.exception("genai import/exec falhou, usando fallback de contexto")
    except Exception:
        logger.exception("genai falhou, usando fallback de contexto")

    # fallback simple
    snippets = "\n\n---\n\n".join([f"Fonte: {s.get('source') or s.get('title') or s.get('id')}\n{s.get('content')[:1000]}" for s in sources[:3]])
    return f"(Fallback) Não foi possível gerar via LLM. Trechos relevantes:\n\n{snippets}\n\nPergunta: {query}"


# FastAPI app
app = FastAPI(title="FRAGAZ Backend", version="0.1")

# Allow CORS for local development so Next.js frontend can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# CORS: Allow frontend dev servers to call the API. Default to permissive
# for local development. Set `FRONTEND_ORIGINS` env to a JSON list or
# comma-separated origins to restrict.
_origins_env = os.environ.get("FRONTEND_ORIGINS")
if _origins_env:
    try:
        import json as _json
        origins = _json.loads(_origins_env) if (_origins_env.strip().startswith("[")) else [o.strip() for o in _origins_env.split(",")]
    except Exception:
        origins = [o.strip() for o in _origins_env.split(",")]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class QueryRequest(BaseModel):
    q: str
    k: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    confidence: Dict
    sources: List[Dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    try:
        logger.info("/query recebido: %s", req.q[:120])
        sources = retrieve_docs(req.q, k=req.k or 5)
        rs = 0.0
        if sources:
            vals = [s.get("score") for s in sources if isinstance(s.get("score"), (int, float))]
            rs = float(sum(vals) / len(vals)) if vals else 0.0

        answer = generate_answer_from_context(req.q, sources)
        confidence = {"Rs": rs, "note": "Rs = média simples dos scores recuperados (0..1)"}
        resp = {"answer": answer, "confidence": confidence, "sources": sources}
        logger.info("Resposta gerada (chars=%d) - Rs=%.3f", len(answer), rs)
        return resp
    except Exception as e:
        logger.exception("Erro no endpoint /query: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# --- OCI helper (basic) -----------------------------------------------------
def get_oci_client():
    """Tenta criar um cliente OCI usando Instance Principals.
    Retorna None se não for possível (caller deve tratar)."""
    try:
        import oci
        from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
        signer = InstancePrincipalsSecurityTokenSigner()
        client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        # valida cliente
        client.get_namespace()
        return client
    except Exception as e:
        logger.warning("OCI client não inicializado: %s", e)
        return None


# --- Endpoint de scraping do Confluence ------------------------------------
class ScrapeConfluenceRequest(BaseModel):
    url: str
    collection_name: Optional[str] = None
    username: Optional[str] = None
    api_token: Optional[str] = None
    title: Optional[str] = None


@app.post("/scrape/confluence")
def scrape_confluence(req: ScrapeConfluenceRequest):
    """Busca uma página Confluence, extrai texto e envia os chunks para o ChromaDB.
    Se `username` e `api_token` forem fornecidos, usa BasicAuth (Confluence Cloud).
    """
    try:
        logger.info("/scrape/confluence solicitado: %s", req.url)
        headers = {"User-Agent": "FRAGAZ-Scraper/1.0"}
        auth = None
        if req.username and req.api_token:
            from requests.auth import HTTPBasicAuth

            auth = HTTPBasicAuth(req.username, req.api_token)

        r = requests.get(req.url, headers=headers, auth=auth, timeout=30)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Falha ao buscar página Confluence: {r.status_code}")

        # extrai texto bruto
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(separator="\n")
        except Exception:
            # fallback simples
            text = r.text

        # gera chunks simples (por parágrafo / tamanho máximo)
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

        # embeddings: tenta usar sentence-transformers, senão fallback determinístico
        embedding_vectors = []
        try:
            from sentence_transformers import SentenceTransformer

            emb_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            for c in chunks:
                vec = emb_model.encode([c])[0].tolist()
                embedding_vectors.append(vec)
        except Exception:
            logger.warning("sentence-transformers não disponível — usando embedding determinístico")
            for c in chunks:
                embedding_vectors.append(_embed_text(c, dim=128))

        # conecta ao Chroma (HTTP preferencial)
        try:
            import chromadb as _chromadb

            chroma_client = None
            try:
                chroma_client = _chromadb.HttpClient(host=os.environ.get("CHROMA_SERVER_IP"), port=int(os.environ.get("CHROMA_SERVER_PORT")), headers={"X-Chroma-Token": os.environ.get("CHROMA_AUTH_TOKEN")})
            except Exception:
                # fallback local client
                chroma_client = _chromadb.Client()

            collection_name = req.collection_name or os.environ.get("COLLECTION_NAME", "fragaz")
            coll = chroma_client.get_or_create_collection(collection_name)

            ids = [f"confluence-{int(time.time())}-{i}" for i in range(len(chunks))]
            metadatas = [{"source": req.url, "title": req.title or req.url, "chunk_index": i} for i in range(len(chunks))]

            coll.add(documents=chunks, metadatas=metadatas, ids=ids, embeddings=embedding_vectors)
            logger.info("Adicionados %d chunks ao Chroma collection=%s", len(chunks), collection_name)
            return {"status": "success", "added": len(chunks), "collection": collection_name}
        except Exception as e:
            logger.exception("Falha ao enviar para Chroma: %s", e)
            raise HTTPException(status_code=500, detail=f"Erro Chroma: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro em /scrape/confluence: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Delegate to the modular app in backend_service
    try:
        import uvicorn
        from backend_service.app import app as imported_app

        reload_flag = os.environ.get("UVICORN_RELOAD", "0") == "1"
        logger.info("Iniciando servidor uvicorn (reload=%s) em http://127.0.0.1:8765", reload_flag)
        uvicorn.run(imported_app, host="127.0.0.1", port=int(os.environ.get("FRAGAZ_PORT", 8765)), reload=reload_flag, log_level="info")
    except Exception as e:
        logger.exception("Erro ao iniciar uvicorn modular: %s", e)
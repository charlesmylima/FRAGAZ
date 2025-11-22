"""Services: chroma, oci, embeddings and index management.

Este módulo centraliza a lógica de acesso ao ChromaDB, OCI e geração de embeddings.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("fragaz.services")

# Integração dos serviços do db_classes
from db_classes.services.usuario_service import UsuarioService
from db_classes.services.login_service import LoginService
from db_classes.services.rotina_service import RotinaService
from db_classes.services.notificacao_service import NotificacaoService
from db_classes.services.log_acao_service import LogAcaoService

ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = ROOT / ".fragaz_index.json"
CHROMA_DIR = ROOT / ".chromadb_fragaz"


def _embed_text(text: str, dim: int = 128) -> List[float]:
    import hashlib

    h = hashlib.sha256(text.encode("utf-8")).digest()
    rep = (dim + len(h) - 1) // len(h)
    buf = (h * rep)[:dim]
    vals = [((b / 255.0) * 2.0 - 1.0) for b in buf]
    return vals


def _cosine_sim(a: List[float], b: List[float]) -> float:
    try:
        import numpy as np

        va = np.array(a, dtype=float)
        vb = np.array(b, dtype=float)
        denom = (np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)
    except Exception:
        dot = sum(x * y for x, y in zip(a, b))
        lena = sum(x * x for x in a) ** 0.5
        lenb = sum(x * x for x in b) ** 0.5
        if lena * lenb == 0:
            return 0.0
        return dot / (lena * lenb)


def load_index() -> List[Dict]:
    if not INDEX_FILE.exists():
        logger.info("Índice local não encontrado: %s", INDEX_FILE)
        return []
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Falha ao carregar índice local: %s", e)
        return []


def get_oci_client():
    try:
        import oci
        from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
        signer = InstancePrincipalsSecurityTokenSigner()
        client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        client.get_namespace()
        return client
    except Exception as e:
        logger.warning("OCI client não inicializado: %s", e)
        return None


def get_chroma_client():
    try:
        import chromadb as _chromadb
        chroma_host = os.environ.get("CHROMA_SERVER_IP")
        chroma_port = os.environ.get("CHROMA_SERVER_PORT")
        chroma_token = os.environ.get("CHROMA_AUTH_TOKEN")
        if chroma_host and chroma_port:
            client = _chromadb.HttpClient(host=chroma_host, port=int(chroma_port), headers={"X-Chroma-Token": chroma_token})
            return client
        try:
            from chromadb.config import Settings as _Settings

            client = _chromadb.Client(_Settings(persist_directory=str(CHROMA_DIR)))
        except Exception:
            client = _chromadb.Client()
        return client
    except Exception as e:
        logger.warning("Chroma client não disponível: %s", e)
        return None


def retrieve_docs(query: str, k: int = 5) -> List[Dict]:
    results = []
    client = get_chroma_client()
    if client:
        try:
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

    entries = load_index()
    if not entries:
        logger.info("Nenhum documento local para recuperar.")
        return []
    # entries expected as dicts with 'embedding'
    qv = _embed_text(query, dim=len(entries[0].get('embedding', [])) if entries and entries[0].get('embedding') else 128)
    scored = [(e, _cosine_sim(qv, e.get('embedding', []))) for e in entries]
    scored.sort(key=lambda t: t[1], reverse=True)
    for e, sc in scored[:k]:
        results.append({
            "id": e.get('id'),
            "title": e.get('title'),
            "content": e.get('content'),
            "source": e.get('source'),
            "score": float(sc),
        })
    logger.info("Recuperado %d docs do índice local", len(results))
    return results


def add_documents_to_chroma(collection_name: str, documents: List[str], metadatas: List[Dict], ids: List[str], embeddings: Optional[List[List[float]]] = None):
    client = get_chroma_client()
    if not client:
        raise RuntimeError("Chroma client não disponível")
    coll = client.get_or_create_collection(collection_name)
    coll.add(documents=documents, metadatas=metadatas, ids=ids, embeddings=embeddings)

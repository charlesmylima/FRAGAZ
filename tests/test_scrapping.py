import pytest
from fastapi.testclient import TestClient
from backend_service.app import app

client = TestClient(app)

# --- Upload e Indexação de Documentos (simulado) ---
def test_upload_pdf_nao_implementado():
    response = client.post("/upload", files={"file": ("doc.pdf", b"%PDF-1.4 fake content")})
    assert response.status_code in (404, 501)

def test_upload_sem_permissao():
    response = client.post("/upload", files={"file": ("doc.pdf", b"%PDF-1.4 fake content")})
    assert response.status_code in (404, 501)

def test_upload_arquivo_corrompido():
    response = client.post("/upload", files={"file": ("doc.exe", b"MZ fake content")})
    assert response.status_code in (404, 501)

# --- Limites: upload muito grande (simulado) ---
def test_upload_arquivo_grande():
    response = client.post("/upload", files={"file": ("big.pdf", b"0" * 1024 * 1024 * 2)})
    assert response.status_code in (404, 501)
import math
from typing import List, Optional
import pytest
from fastapi.testclient import TestClient

from backend_service.app import app

client = TestClient(app)

# --- Busca retorna múltiplos documentos ---
def test_busca_multiplos_documentos():
    client.post("/usuarios", json={"nome": "BuscaMulti", "email": "multi@fragaz.com", "senha": "senhaSegura123"})
    login = client.post("/token", data={"username": "multi@fragaz.com", "password": "senhaSegura123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/busca", params={"q": "doc"}, headers=headers)
    assert response.status_code == 200
    assert "doc1" in response.text and "doc2" in response.text

# --- Busca retorna nenhum resultado ---
def test_busca_sem_resultado():
    client.post("/usuarios", json={"nome": "BuscaZero", "email": "zero@fragaz.com", "senha": "senhaSegura123"})
    login = client.post("/token", data={"username": "zero@fragaz.com", "password": "senhaSegura123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/busca", params={"q": "nada"}, headers=headers)
    assert response.status_code == 200
    assert "resultados" in response.text
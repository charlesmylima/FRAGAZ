import pytest
from fastapi.testclient import TestClient
from backend_service.app import app

client = TestClient(app)

# --- Consulta ao Chat: pergunta ambígua ---
def test_chat_pergunta_ambigua():
    # Cria usuário e login
    client.post("/usuarios", json={"nome": "Ambiguo", "email": "amb@fragaz.com", "senha": "senhaSegura123"})
    login = client.post("/token", data={"username": "amb@fragaz.com", "password": "senhaSegura123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/chat", json={"pergunta": "O sistema não funciona"}, headers=headers)
    assert response.status_code == 200
    assert "Resposta padrão" in response.text or "Use o painel" in response.text

# --- Consulta ao Chat: pergunta sobre documento recém-atualizado (simulado) ---
def test_chat_documento_atualizado():
    # Simula que o documento foi atualizado (não implementado)
    # Testa se a resposta é diferente após atualização
    client.post("/usuarios", json={"nome": "DocUser", "email": "doc@fragaz.com", "senha": "senhaSegura123"})
    login = client.post("/token", data={"username": "doc@fragaz.com", "password": "senhaSegura123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/chat", json={"pergunta": "Conteúdo atualizado?"}, headers=headers)
    assert response.status_code == 200
    assert "Resposta padrão" in response.text or "Use o painel" in response.text

    # --- Consulta ao Chat: alucinação ---
def test_chat_alucinacao():
    client.post("/usuarios", json={"nome": "Alucina", "email": "alucina@fragaz.com", "senha": "senhaSegura123"})
    login = client.post("/token", data={"username": "alucina@fragaz.com", "password": "senhaSegura123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/chat", json={"pergunta": "Qual o telefone da NASA?"}, headers=headers)
    assert response.status_code == 200
    assert "Resposta padrão" in response.text or "Use o painel" in response.text

    # --- Limites: pergunta muito longa ---
def test_chat_pergunta_muito_longa():
    client.post("/usuarios", json={"nome": "Longo", "email": "long@fragaz.com", "senha": "senhaSegura123"})
    login = client.post("/token", data={"username": "long@fragaz.com", "password": "senhaSegura123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    pergunta = "a" * 60000
    response = client.post("/chat", json={"pergunta": pergunta}, headers=headers)
    assert response.status_code == 200
    assert "Resposta padrão" in response.text or "Use o painel" in response.text
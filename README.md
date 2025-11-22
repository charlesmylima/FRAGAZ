## Testes Automatizados (Pytest)

O projeto inclui uma bateria de testes automatizados para backend, segurança, limites e casos de uso do sistema. Para rodar todos os testes:

```pwsh
pytest tests
```

Principais testes implementados:

- **Autenticação e Usuário:**
  - Criação de usuário (senha forte, e-mail duplicado)
  - Login (credenciais válidas, senha errada, usuário inativo)
- **Chat (RAG):**
  - Pergunta normal, ambígua, alucinação, documento atualizado (simulado)
  - Pergunta muito longa
  - Prompt Injection
- **Busca:**
  - Busca por palavra-chave
  - Busca com múltiplos resultados
  - Busca sem resultados
  - SQL Injection
- **Upload de Documentos (simulado):**
  - Upload de PDF válido
  - Upload sem permissão
  - Upload de arquivo corrompido ou formato não suportado
  - Upload muito grande
- **Recuperação de Senha, Notificações, Sessão (simulado):**
  - Recuperação de senha não implementada
  - Notificações e desativação (não implementado)
  - Sessão expirada (não implementado)
- **Concorrência:**
  - Login múltiplo (simulado)

Os testes estão distribuídos nos arquivos:
- `tests/test_auth.py` — autenticação, segurança, recuperação de senha
- `tests/test_chat.py` — chat, perguntas, limites
- `tests/test_db.py` — busca
- `tests/test_scores.py` — funções de score e métricas
- `tests/test_scrapping.py` — upload de documentos e limites

Para garantir cobertura, execute todos os testes antes de submissão.
# FRAGAZ — PoC RAG (Next.js + FastAPI)

Este repositório agora referencia a arquitetura atual do PoC: um frontend desacoplado em **Next.js** (React) e um backend em **FastAPI** (Python). Abaixo há um resumo da nova arquitetura, instruções de execução e notas sobre a versão inicial baseada em Streamlit e as dificuldades observadas durante a modelagem do PoC.

## Resumo rápido

- **Frontend:** Next.js app com duas telas principais — **Painel** (lista/preview de documentos indexados) e **Chat** (conversas e consultas RAG).
- **Backend:** `backend.py` (FastAPI) expõe `/query` e endpoints auxiliares; tenta usar ChromaDB quando habilitado e Gemini/GenAI quando a chave está disponível; caso contrário, usa um índice local persistido (`.fragaz_index.json`) como fallback.
- **Objetivo:** oferecer um demo local simples e robusto para avaliação, com fallbacks claros quando dependências externas não estiverem disponíveis.

## Histórico e lições (versão inicial com Streamlit)

Na primeira iteração do PoC a interface foi embarcada em uma aplicação Streamlit que injetava um `index.html` React. Essa abordagem facilitou prototipação (um único processo Python que servia UI e backend), porém trouxe dificuldades que motivaram a migração para a arquitetura atual:

- **Limitação no controle cliente/servidor:** Streamlit simplifica a entrega, mas complica cenários onde desejamos um SPA React com rotas, hydration e chamadas HTTP diretas ao backend.
- **Problemas operacionais com dependências pesadas:** bibliotecas opcionais (Chroma, `tiktoken`, clients de LLM) exigem toolchains nativos e tornaram a execução reprodutível mais difícil em ambientes heterogêneos.

Por esses motivos migramos o frontend para Next.js (desacoplado) e mantivemos um backend Python (FastAPI) leve e previsível.

## Instruções rápidas

Leia o README completo abaixo para mais detalhes, ou siga os passos de "Quickstart" para executar localmente.

---

**FRAGAZ — Protótipo Híbrido (Streamlit + React)**

Este repositório apresenta uma prova de conceito do FRAGAZ — assistente help‑desk baseado em RAG (Retrieval Augmented Generation). Nesta entrega adotamos uma solução híbrida deliberada: o backend e orquestração são implementados em Python com Streamlit, enquanto a interface de usuário de controle semântico e responsivo foi desenvolvida em React (via CDN) e é embutida na aplicação Streamlit.

Visão geral e motivação
-----------------------
Streamlit é um excelente framework para prototipagem rápida e para expor lógica Python (ingestão, indexação, consulta). Contudo, o requisito acadêmico do Módulo 2 exige controle explícito sobre a semântica do HTML e sobre a estratégia de CSS responsivo — coisas que são mais facilmente garantidas quando se tem controle direto do markup (tags `<main>`, `<section>`, `<form>`, etc.) e de folhas de estilo entregues juntamente com a UI.

A solução adotada combina os pontos fortes de ambas as abordagens:
- Streamlit: atua como servidor/orquestrador Python, executa a ingestão (`backend.py`), gera/expõe o índice e disponibiliza endpoints locais; também serve a página React embutida.
- React (via CDN): fornece o `index.html` com marcação semântica, componentes interativos e CSS responsivo customizado. Este `index.html` é injetado em Streamlit através de `st.components.v1.html`, mantendo um único processo de execução e garantindo que os requisitos do Módulo 2 sejam atendidos.

Conteúdo do repositório
-----------------------
- `backend.py`: ingestão local, chunking, geração de embeddings (fallback determinístico e caminho opcional para provedores via `GEMINI_API_KEY`), persistência em `.fragaz_index.json` e integração condicional com ChromaDB.
- `frontend/index.html`: interface React (CDN) com marcação semântica e imports de `styles.css` (responsividade). Este arquivo é renderizado dentro do Streamlit usando `st.components.v1.html`.
- `frontend/streamlit_app.py`: app Streamlit que injeta o `index.html`, expõe a UI e conecta chamadas de frontend ao backend Python.
- `frontend/ui_helpers.py`, `frontend/screens/*`: helpers e telas auxiliares para quem preferir executar a UI nativamente em Streamlit.
- `arquivos/`: documentos para ingestão (ex.: `exemplo.txt`).
- `.fragaz_index.json`: índice persistido gerado pela ingestão.
- `./.chromadb_fragaz/collection.jsonl`: fallback criado quando `chromadb` não está disponível.
- `requirements.txt`: dependências do projeto.

Arquitetura e fluxo de execução
-------------------------------
1. O usuário abre a aplicação Streamlit (`streamlit run frontend/streamlit_app.py`).
2. Streamlit injeta o `frontend/index.html` (React) usando `st.components.v1.html`, garantindo que a UI entregue HTML semântico e CSS customizado.
3. A UI (React) envia solicitações (ex.: via fetch/POST) ao código Python em `backend.py` exposto por rotinas locais (p. ex. endpoints simples ou handlers invocados pelo componente embutido), solicitando busca por trechos, ingestão ou ações administrativas.
4. `backend.py` processa a ingestão (chunking), gera embeddings (Gemini quando configurado, senão fallback), persiste o índice e responde com trechos relevantes que a UI exibe.

Justificativa técnica
---------------------
- Controle semântico do HTML: o arquivo `index.html` contém a marcação que atende explicitamente ao requisito de HTML semântico (uso de `<main>`, `<section>`, `<form>` e elementos de formulário semânticos).
- CSS responsivo: o CSS aplicado diretamente ao `index.html` (e carregado junto com a UI) permite regras de mídia, grids e controles de layout que garantem comportamento consistente em mobile e desktop — algo que seria mais trabalhoso e limitado apenas com componentes nativos do Streamlit.
- Simplicidade operacional: a injeção de HTML mantém o fluxo de desenvolvimento em uma única aplicação Python, simples de executar para a entrega acadêmica, sem necessidade de servidor web adicional.

Validação dos requisitos do Módulo 2
------------------------------------
Esta seção documenta, de forma objetiva, como cada requisito foi atendido na solução híbrida.

- Uso de um framework: Implementado.
  - Justificativa: Streamlit é o framework utilizado como orquestrador e servidor da aplicação (backend Python). A interface foi construída em React (via CDN) e embutida pelo Streamlit para garantir controle total sobre o HTML.

- Estruturação correta com HTML (Semântica): Implementado.
  - Justificativa: A marcação semântica exigida foi implementada diretamente no `frontend/index.html` (React). Em vez de depender exclusivamente da abstração do Streamlit, entregamos HTML puro com `<main>`, `<section>`, `<form>` e elementos de formulário semânticos para cumprir o requisito.

- Estilização responsiva com CSS: Implementado.
  - Justificativa: O CSS customizado anexado ao `index.html` garante adaptação a diferentes larguras e dispositivos (media queries, flex/grid). Esta abordagem fornece controle preciso sobre acessibilidade e responsividade que complementa a capacidade de prototipagem do Streamlit.

Como executar (PowerShell)
--------------------------
1) Criar e ativar um venv (recomendado):

```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Instalar dependências (usar `--no-cache-dir` se houver problemas de permissão):

```pwsh
$env:PIP_NO_CACHE_DIR = "1"
pip install --no-cache-dir -r requirements.txt
```

3) Gerar índice (ingestão de `arquivos/`):

```pwsh
python backend.py
```

4) Iniciar a interface (Streamlit injeta o React embutido):

```pwsh
streamlit run frontend/streamlit_app.py
```

Notas operacionais e boas práticas
---------------------------------
- Não comite chaves/segredos: use `GEMINI_API_KEY` via variável de ambiente quando necessário.
- Arquivos gerados (`.fragaz_index.json` e `.chromadb_fragaz/`) podem ser adicionados ao `.gitignore` (já configurado).
- Se `chromadb` não puder ser instalado no ambiente do avaliador, o pipeline usa um fallback (arquivo JSONL) que preserva a capacidade de demonstração do RAG.

HTML semântico para submissão (Prova acadêmica)
----------------------------------------------
Para facilitar a avaliação do Módulo 2, este repositório inclui uma versão estática e semântica da interface que evidencia o uso correto de tags HTML e de CSS responsivo.

- Arquivo para submissão: `frontend/semantic_interface.html`
  - Contém marcação semântica (`<main>`, `<header>`, `<nav>`, `<section>`, `<article>`, `<aside>`, `<footer>`), atributos ARIA e exemplos de formulários e resultados.
  - Usa o mesmo `styles.css` do projeto para demonstrar responsividade.

Como gerar o PDF para submissão:

1. Abra `frontend/semantic_interface.html` no navegador (duplo clique ou `File > Open`).
2. Revise a aparência e, se desejar, inspecione o DOM com DevTools para confirmar a semântica.
3. No menu do navegador: escolha `Imprimir` → `Salvar como PDF` (ou `Export to PDF`).
4. Anexe o PDF gerado ao relatório acadêmico e inclua a justificativa técnica (seção "Justificativa técnica" neste README).

Esta página é fornecida como evidência direta do cumprimento dos requisitos de HTML semântico e CSS responsivo do Módulo 2.

Padrões de Git e commits
------------------------
Mantivemos a convenção baseada em Conventional Commits para clareza e rastreabilidade:

Formato: `<tipo>(<módulo>): descrição curta em infinitivo`

Exemplos:
- `feat(frontend): adicionar campo de pesquisa em linguagem natural`
- `fix(backend): corrigir cálculo de similaridade cosseno`

Branches sugeridas:
- `main`, `develop`, `feature/*`, `release/*`, `hotfix/*` — fluxo simples para colaboração.

Próximos passos planejados
-------------------------
- Validar `chromadb` em ambientes heterogêneos e documentar versão mínima recomendada.
- Adicionar testes automatizados e pipeline CI para garantir reprodutibilidade.
- Opcional: extrair uma SPA React independente (deploy separado) para demonstrar arquitetura desacoplada.

Contato e submissão
-------------------
Este repositório é a entrega para o Projeto Integrador II. Para dúvidas sobre execução ou avaliação, abra uma issue ou envie mensagem ao autor no repositório.


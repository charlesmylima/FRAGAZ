FRAGAZ Next.js frontend

This folder contains a minimal Next.js app that serves as the new FRAGAZ frontend.

Quick start (from project root):

1. Install dependencies (Node.js + npm required):

```bash
cd frontend/next_app
npm install
```

2. Start the Python backend (index must exist) and the local API:

```pwsh
# from repository root: generate the index
python backend.py

# then start the local Python API helper (keeps process alive):
python frontend/run_local_api.py

# (Alternatively you can start the API with the one-liner:)
python -c "from frontend.local_api import start_local_api; start_local_api(); import time; time.sleep(1e9)"
```

3. Start Next dev server:

```bash
npm run dev
```

- Panel page: `http://localhost:3000/` shows the latest documents read from `.fragaz_index.json`.
- Chat page: `http://localhost:3000/chats` manages multiple conversations and sends queries to `http://127.0.0.1:8765/query`.

Notes:
- The Next app reads `.fragaz_index.json` on the server side (getServerSideProps) so run `python backend.py` first to generate the index.
- The chat page relies on the lightweight Python local API available at port 8765. Ensure it is running.

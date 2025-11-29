**MumbaiHacks-HyperCube — Token Assigner & Merchant Dashboard**

**Youtube Video Link: https://youtu.be/X8pXUTrserw?si=tlM1BX3Os_ONv6HQ**        

**Presentation Link: https://www.canva.com/design/DAG6CPu7of4/eF9RkEPcQNThut6QLn7b9A/view?utm_content=DAG6CPu7of4&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h1504286478**

One-line: Real-time token issuance, risk-driven token lifecycle, and a React merchant dashboard.

**Features**
- **Real-time tokens**: Issue tokens and push updates via `Socket.IO`.
- **Token lifecycle**: Idempotent creation, `active`/`frozen`/`revoked` states with TTL cleanup.
- **Risk integration**: API endpoints for agents to `freeze`/`revoke` tokens (agentic risk workflows).
- **Frontend dashboard**: React UI with payment simulation, live tokens table, and detail panel.
- **Simple auth**: API-key based auth for demo workflows.
- **Production-ready patterns**: Idempotency keys, audit-friendly APIs, and modular routes.

**Quick Start (local)**
- Prereqs: `Python 3.8+`, `pip`, `Node.js 16+`, `npm`, `MongoDB`.

1) Backend (Token Assigner)

```powershell
cd backend
pip install -r requirements.txt
# copy or create .env from .env.example and set MONGO_URL, MONGO_DB, MERCHANT_AUTH_KEY
uvicorn token_assigner:asgi_app --reload --port 8000
```

Backend default: `http://localhost:8000` — docs at `/docs`.

2) Frontend (Merchant Dashboard)

```powershell
cd frontend
npm install
npm run dev
```

Frontend default: `http://localhost:5173` (Vite).

**Minimal Usage Examples**
- Create token (API): `POST /assign-token` with merchant/payload and `Authorization: Bearer <KEY>`.
- Freeze token (Agent): `POST /freeze-token` with `token_id`.
- Real-time events: listen to `token.assigned`, `token.frozen`, `token.revoked` on namespace `/merchant`.

**Important Files**
- Backend: `backend/token_assigner.py`, `backend/app/main.py`, `backend/requirements.txt`
- Frontend: `frontend/package.json`, `frontend/src/App.jsx`, `frontend/src/socket.js`, `frontend/src/SimulatePayment.jsx`
- Risk service docs: `risk-service/README_ROBUST_API.md` and `risk-service/app.py`

**Environment (example variables)**
- `MONGO_URL` — MongoDB connection string
- `MONGO_DB` — database name
- `MERCHANT_AUTH_KEY` — demo API key used by frontend / curl
- (optionally) `GROQ_API_KEY` for agent integrations in `risk-service`

**Notes & Next Steps**
- Use the `idempotency_key` field when creating tokens to avoid duplicates.
- For production, configure CORS origins, HTTPS, and a proper secrets store.
- Consider running `pytest` in `risk-service` for the robust API test suite.

**Contact / Help**
- If you want, I can: run tests, update the root `README.md` with this concise version, or commit the file.

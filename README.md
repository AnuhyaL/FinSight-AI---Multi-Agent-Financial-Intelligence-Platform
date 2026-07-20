# FinSight AI — Multi-Agent Financial Analyst

FinSight AI is a portfolio-ready financial-intelligence platform that turns annual reports into cited answers, transparent risk scoring, revenue forecasts, sentiment signals, investment recommendations, and competitor comparisons. It is an analytical aid—not financial advice.

## Architecture and capabilities

The React/Vite frontend calls a typed FastAPI service. PDF reports are extracted with PyMuPDF, chunked with LangChain splitters, embedded by Sentence Transformers, and retrieved from persistent Chroma collections. Groq + Llama 3 generates grounded responses when configured. A LangGraph workflow orchestrates risk, revenue, sentiment, and recommendation specialists.

| Capability | Endpoint |
| --- | --- |
| Upload and index report | `POST /api/v1/reports/upload` |
| Cited RAG chat | `POST /api/v1/chat` |
| Risk / forecast / sentiment | `POST /api/v1/analysis/{risk,forecast,sentiment}` |
| Recommendation / competitors | `POST /api/v1/analysis/{recommendation,competitors}` |
| PDF export of a report's analysis | `GET /api/v1/reports/{report_id}/export/pdf` |

## Folder structure

```text
FinSight-AI/
├── backend/        # FastAPI, agents, RAG, forecasting, tests
├── frontend/       # Vite + React + Tailwind premium dashboard
├── requirements.txt
├── render.yaml     # Render blueprint
└── .env.example
```

## Local installation

Requires Python 3.11+ and Node.js 20+.

```bash
git clone <your-repository-url>
cd FinSight-AI
python -m venv .venv
# Windows: .venv\Scripts\activate   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # macOS/Linux: cp .env.example .env
uvicorn backend.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`; API documentation is available at `http://localhost:8000/docs`.

## Environment variables

`GROQ_API_KEY` enables Llama 3 RAG answers; without it chat returns the retrieved evidence safely. `GROQ_MODEL`, `EMBEDDING_MODEL`, `FINBERT_MODEL`, `CORS_ORIGINS`, `CHROMA_DIR`, `REPORTS_DIR`, and `MAX_UPLOAD_MB` all have documented defaults in `.env.example`. Large Hugging Face models download on first use; the sentiment agent has a lightweight fallback for unavailable models.

## Testing

```bash
pytest backend/tests -q
python -m compileall backend
cd frontend && npm run build
```

Tests cover PDF extraction, agents, forecasting, API health, and missing-report RAG behavior. Add API-key integration tests separately in CI secrets.

## Deployment

### Backend — Render

Push this repository to GitHub, create a Render Blueprint from `render.yaml`, then set `GROQ_API_KEY` and `CORS_ORIGINS` to the Vercel URL. Render’s ephemeral filesystem means report/vector persistence should move to object storage and managed Chroma/Postgres for production multi-instance deployments.

### Frontend — Vercel

Import the repository, set the project root to `frontend`, build command to `npm run build`, output directory to `dist`, and add `VITE_API_BASE_URL=https://<render-service>.onrender.com`.

## Troubleshooting

- **CORS error:** set `CORS_ORIGINS` exactly to the frontend origin.
- **Chat says report missing:** upload the PDF to the same backend instance first.
- **Model download or memory issue:** set a smaller embedding model; the FinBERT fallback remains available.
- **Prophet install issue:** use Python 3.11 and upgrade pip before installing requirements.
- **No text in PDF:** upload a text-based report or add OCR before ingestion.

## Recruiter project summary

FinSight AI demonstrates production-oriented AI engineering: grounded retrieval with citations, provider-resilient LLM integration, LangGraph orchestration, interpretable financial scoring, asynchronous-safe FastAPI boundaries, a polished responsive frontend, tests, deployment manifests, and operational configuration. Screenshots can be added here after deployment.

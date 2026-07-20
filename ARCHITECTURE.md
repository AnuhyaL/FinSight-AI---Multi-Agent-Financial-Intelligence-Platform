# FinSight AI Architecture

```text
React + Vite dashboard ──REST──> FastAPI API
                                      │
                 ┌────────────────────┼────────────────────┐
                 │                    │                    │
            Report ingestion       Analysis agents       RAG chat
        PyMuPDF/pdfplumber       risk/forecast/etc.  Chroma + embeddings
                 │                    │                    │
             local reports       deterministic metrics  Groq Llama 3
```

The API is stateless apart from report PDFs and Chroma persistence, so it can be deployed as a Render web service. Expensive ML integrations are lazy-loaded and have deterministic fallbacks, allowing development and tests without model downloads or provider keys. The frontend is a static Vercel deployment configured with `VITE_API_BASE_URL`.

from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from backend.agents.competitor_agent import compare_companies
from backend.agents.investment_agent import recommend_investment
from backend.agents.revenue_agent import analyze_revenue
from backend.agents.risk_agent import analyze_risk
from backend.agents.sentiment_agent import analyze_sentiment
from backend.chat import answer_question
from backend.config import settings
from backend.export import build_pdf
from backend.models import ChatRequest, CompetitorRequest, FinancialMetrics, RecommendationRequest, SentimentRequest
from backend.rag.chunking import chunk_pages
from backend.rag.pdf_parser import extract_pdf_pages
from backend.rag.vector_store import index_chunks, search
from backend.services import extract_latest_fiscal_year, extract_metrics, health_score
from backend.workflow import build_analysis_graph

router = APIRouter(prefix="/api/v1")
_analysis_graph = build_analysis_graph()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "FinSight AI"}


@router.post("/reports/upload")
async def upload_report(file: UploadFile = File(...)) -> dict:
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(415, "Upload a PDF annual report.")
    content = await file.read()
    if not content or len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "File is empty or exceeds the upload limit.")
    report_id = str(uuid4())
    path = settings.resolved_reports_dir() / f"{report_id}.pdf"
    path.write_bytes(content)
    try:
        pages = extract_pdf_pages(path); chunks = chunk_pages(pages)
        indexed = index_chunks(report_id, chunks)
    except (ValueError, FileNotFoundError) as exc:
        path.unlink(missing_ok=True); raise HTTPException(422, str(exc)) from exc
    # Financial statements often occur after the introductory pages of a 10-K.
    full_text = "\n".join(page.text for page in pages)
    metrics = extract_metrics(full_text)
    return {"report_id": report_id, "filename": file.filename, "pages": len(pages), "chunks_indexed": indexed,
            "preliminary_metrics": metrics.model_dump(), "latest_fiscal_year": extract_latest_fiscal_year(full_text)}


@router.get("/reports/{report_id}/excerpts")
def report_excerpts(report_id: str, limit: int = 5) -> dict:
    """Real, report-specific passages for pre-filling sentiment analysis, so results differ
    per company instead of relying on whatever generic text a user leaves in the textarea."""
    try:
        results = search(report_id, "financial performance, outlook, and business risks", limit=limit)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"excerpts": [item["text"] for item in results]}


@router.get("/reports/{report_id}/export/pdf")
def export_pdf(report_id: str) -> Response:
    path = settings.resolved_reports_dir() / f"{report_id}.pdf"
    if not path.exists():
        raise HTTPException(404, "Report not found.")
    pages = extract_pdf_pages(path)
    full_text = "\n".join(page.text for page in pages)
    metrics = extract_metrics(full_text)
    latest_year = extract_latest_fiscal_year(full_text)
    history = metrics.revenue_history or [metrics.revenue, metrics.revenue]
    metrics_with_history = metrics.model_copy(update={"revenue_history": history})
    risk_result = analyze_risk(metrics_with_history)
    revenue_result = analyze_revenue(history, latest_year)
    try:
        sentiment_texts = [item["text"] for item in search(report_id, "financial performance, outlook, and business risks", limit=5)]
    except LookupError:
        sentiment_texts = ["neutral market coverage"]
    sentiment_result = analyze_sentiment(sentiment_texts)
    recommendation = recommend_investment(risk_result, revenue_result, sentiment_result, health_score(metrics))
    pdf_bytes = build_pdf(path.name, metrics, risk_result, revenue_result, sentiment_result, recommendation,
                           health_score(metrics))
    return Response(content=pdf_bytes, media_type="application/pdf",
                     headers={"Content-Disposition": f'attachment; filename="{report_id}-finsight-report.pdf"'})


@router.post("/chat")
def chat(request: ChatRequest) -> dict:
    try: return answer_question(request.report_id, request.question)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@router.post("/analysis/risk")
def risk(metrics: FinancialMetrics) -> dict: return analyze_risk(metrics)


@router.post("/analysis/forecast")
def forecast(metrics: FinancialMetrics, latest_year: int | None = None) -> dict:
    try: return analyze_revenue(metrics.revenue_history, latest_year)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc


@router.post("/analysis/sentiment")
def sentiment(request: SentimentRequest) -> dict: return analyze_sentiment(request.texts)


@router.post("/analysis/recommendation")
def recommendation(request: RecommendationRequest) -> dict:
    """Fans out to the risk, revenue, and sentiment agents via LangGraph, then merges into a recommendation."""
    try:
        state = _analysis_graph.invoke({"metrics": request.metrics, "sentiment_texts": request.sentiment_texts,
                                         "latest_year": request.latest_year})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"risk": state["risk"], "revenue": state["revenue"], "sentiment": state["sentiment"],
            "health_score": state["health"], "recommendation": state["recommendation"]}


@router.post("/analysis/competitors")
def competitors(request: CompetitorRequest) -> dict: return compare_companies(request.companies)

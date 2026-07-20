from fastapi.testclient import TestClient
from backend.main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_export_pdf_for_missing_report_returns_404() -> None:
    response = TestClient(app).get("/api/v1/reports/not-a-real-id/export/pdf")
    assert response.status_code == 404


def test_recommendation_endpoint_merges_agent_outputs() -> None:
    payload = {"metrics": {"revenue": 100, "net_income": 20, "assets": 200, "liabilities": 60,
                            "operating_cash_flow": 25, "revenue_history": [70, 85, 100]},
               "sentiment_texts": ["Strong profit growth and positive outlook"]}
    response = TestClient(app).post("/api/v1/analysis/recommendation", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["recommendation"]["recommendation"] in {"BUY", "HOLD", "SELL"}
    assert {"risk", "revenue", "sentiment", "health_score", "recommendation"} <= body.keys()

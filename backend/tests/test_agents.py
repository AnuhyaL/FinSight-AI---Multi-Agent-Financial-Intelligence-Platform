from backend.agents.competitor_agent import compare_companies
from backend.agents.risk_agent import analyze_risk
from backend.agents.sentiment_agent import analyze_sentiment
from backend.models import FinancialMetrics


def sample_metrics() -> FinancialMetrics:
    return FinancialMetrics(revenue=100, net_income=20, assets=200, liabilities=60,
                            operating_cash_flow=25, revenue_history=[70, 85, 100])


def test_risk_is_bounded() -> None:
    result = analyze_risk(sample_metrics())
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] == "Low"


def test_sentiment_fallback_result() -> None:
    result = analyze_sentiment(["Strong profit growth and positive outlook"])
    assert result["sentiment"] in {"positive", "neutral", "negative"}


def test_competitor_comparison() -> None:
    result = compare_companies({"Alpha": sample_metrics(), "Beta": sample_metrics()})
    assert len(result["companies"]) == 2

from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from backend.agents.investment_agent import recommend_investment
from backend.agents.revenue_agent import analyze_revenue
from backend.agents.risk_agent import analyze_risk
from backend.agents.sentiment_agent import analyze_sentiment
from backend.models import FinancialMetrics
from backend.services import health_score


class AnalysisState(TypedDict, total=False):
    metrics: FinancialMetrics
    sentiment_texts: list[str]
    latest_year: int | None
    risk: dict
    revenue: dict
    sentiment: dict
    health: float
    recommendation: dict


def build_analysis_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("risk", lambda state: {"risk": analyze_risk(state["metrics"])})
    graph.add_node("revenue", lambda state: {"revenue": analyze_revenue(
        state["metrics"].revenue_history or [state["metrics"].revenue] * 2, state.get("latest_year"))})
    graph.add_node("sentiment", lambda state: {"sentiment": analyze_sentiment(state.get("sentiment_texts", ["neutral market coverage"]))})
    graph.add_node("recommend", lambda state: {"health": health_score(state["metrics"]), "recommendation": recommend_investment(state["risk"], state["revenue"], state["sentiment"], health_score(state["metrics"]))})
    graph.add_edge(START, "risk"); graph.add_edge(START, "revenue"); graph.add_edge(START, "sentiment")
    graph.add_edge("risk", "recommend"); graph.add_edge("revenue", "recommend"); graph.add_edge("sentiment", "recommend")
    graph.add_edge("recommend", END)
    return graph.compile()

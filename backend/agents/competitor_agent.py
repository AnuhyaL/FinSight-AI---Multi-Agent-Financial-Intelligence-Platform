from backend.models import FinancialMetrics
from .risk_agent import analyze_risk


def compare_companies(companies: dict[str, FinancialMetrics]) -> dict:
    rows = []
    for name, metrics in companies.items():
        risk = analyze_risk(metrics)
        growth = risk["revenue_growth_pct"]
        health = max(0, min(100, 80 - risk["risk_score"] + max(-10, min(10, growth))))
        rows.append({"company": name, "revenue": metrics.revenue, "net_income": metrics.net_income,
                     "risk_score": risk["risk_score"], "growth_pct": growth, "health_score": round(health, 1)})
    return {"companies": rows, "leader": max(rows, key=lambda row: row["health_score"])["company"]}

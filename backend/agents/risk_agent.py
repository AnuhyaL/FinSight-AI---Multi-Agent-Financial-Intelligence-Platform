from backend.models import FinancialMetrics


def analyze_risk(metrics: FinancialMetrics, business_risks: list[str] | None = None) -> dict:
    """Score balance-sheet and cash-flow risk on a transparent 0-100 scale."""
    debt_ratio = metrics.liabilities / metrics.assets if metrics.assets else 0.5
    revenue_change = 0.0
    if len(metrics.revenue_history) >= 2 and metrics.revenue_history[-2]:
        revenue_change = ((metrics.revenue_history[-1] / metrics.revenue_history[-2]) - 1) * 100
    cash_ratio = metrics.operating_cash_flow / metrics.net_income if metrics.net_income else 0
    score = min(100, max(0, 20 + debt_ratio * 45 + max(0, -revenue_change) * 1.5
                         + (15 if cash_ratio < 0.75 else 0) + min(15, len(business_risks or []) * 2)))
    level = "High" if score >= 65 else "Medium" if score >= 35 else "Low"
    return {"risk_score": round(score, 1), "risk_level": level,
            "debt_ratio": round(debt_ratio, 3), "revenue_growth_pct": round(revenue_change, 2),
            "explanation": f"{level} risk: debt ratio is {debt_ratio:.1%}; revenue trend is {revenue_change:.1f}%.",
            "risk_factors": business_risks or []}

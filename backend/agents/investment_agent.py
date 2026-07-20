def recommend_investment(risk: dict, revenue: dict, sentiment: dict, health_score: float) -> dict:
    sentiment_points = {"positive": 15, "neutral": 0, "negative": -15}.get(sentiment["sentiment"], 0)
    score = max(0, min(100, health_score - risk["risk_score"] * .35 + sentiment_points + (10 if revenue["trend"] == "growing" else -10)))
    recommendation = "BUY" if score >= 65 else "HOLD" if score >= 40 else "SELL"
    return {"recommendation": recommendation, "investment_score": round(score, 1),
            "reasoning": f"{recommendation} based on health {health_score:.0f}/100, {risk['risk_level'].lower()} risk, {sentiment['sentiment']} sentiment, and {revenue['trend']} revenue."}

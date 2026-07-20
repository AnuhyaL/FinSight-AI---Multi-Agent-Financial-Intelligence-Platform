from backend.forecasting.revenue_forecasting import forecast_revenue


def analyze_revenue(history: list[float], latest_year: int | None = None) -> dict:
    result = forecast_revenue(history, latest_year=latest_year)
    result["latest_revenue"] = history[-1]
    result["growth_opportunity"] = "Expansion potential is positive." if result["trend"] == "growing" else "Focus on retention and margin resilience."
    return result

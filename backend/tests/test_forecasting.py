from backend.forecasting.revenue_forecasting import forecast_revenue


def test_revenue_forecast_shape() -> None:
    result = forecast_revenue([100, 110, 121], periods=3)
    assert len(result["forecast"]) == 3
    assert result["trend"] in {"growing", "contracting"}


def test_forecast_years_follow_the_filings_latest_fiscal_year() -> None:
    result = forecast_revenue([383285, 391035, 416161], periods=3, latest_year=2025)
    assert result["forecast_years"] == [2026, 2027, 2028]

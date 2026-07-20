from datetime import datetime
import pandas as pd


def forecast_revenue(history: list[float], periods: int = 4, latest_year: int | None = None) -> dict:
    """Forecast annual revenue using Prophet when sufficient history exists.

    `history` is chronological (oldest first), one figure per fiscal year, ending in
    `latest_year` (defaulting to the current calendar year when the filing's fiscal year
    isn't known). Forecasting quarters from annual figures would misread 12-month gaps
    between data points as 3-month ones, so both the historical index and the future
    horizon use annual frequency.
    """
    if len(history) < 2:
        raise ValueError("At least two revenue observations are required.")
    end_year = latest_year or datetime.now().year
    start_year = end_year - len(history) + 1
    dates = pd.date_range(f"{start_year}-12-31", periods=len(history), freq="YE")
    frame = pd.DataFrame({"ds": dates, "y": history})
    try:
        from prophet import Prophet
        model = Prophet(weekly_seasonality=False, daily_seasonality=False, yearly_seasonality=False)
        model.fit(frame)
        future = model.make_future_dataframe(periods=periods, freq="YE")
        prediction = model.predict(future).tail(periods)
        values = prediction["yhat"].clip(lower=0).round(2).tolist()
        lower = prediction["yhat_lower"].clip(lower=0).round(2).tolist()
        upper = prediction["yhat_upper"].clip(lower=0).round(2).tolist()
    except (ImportError, ValueError):
        growth = history[-1] / history[-2] - 1 if history[-2] else 0
        values = [round(history[-1] * (1 + growth) ** i, 2) for i in range(1, periods + 1)]
        lower, upper = [round(v * .9, 2) for v in values], [round(v * 1.1, 2) for v in values]
    forecast_years = [end_year + i for i in range(1, periods + 1)]
    return {"forecast": values, "lower_bound": lower, "upper_bound": upper, "forecast_years": forecast_years,
            "trend": "growing" if values[-1] >= history[-1] else "contracting"}

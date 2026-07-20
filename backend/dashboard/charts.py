import plotly.graph_objects as go


def revenue_forecast_figure(history: list[float], forecast: list[float]) -> dict:
    """Return a JSON-safe interactive Plotly revenue figure."""
    figure = go.Figure()
    figure.add_scatter(x=list(range(1, len(history) + 1)), y=history, mode="lines+markers", name="Actual")
    figure.add_scatter(x=list(range(len(history) + 1, len(history) + len(forecast) + 1)), y=forecast, mode="lines+markers", name="Forecast", line={"dash": "dash"})
    figure.update_layout(template="plotly_dark", title="Revenue forecast", xaxis_title="Period", yaxis_title="Revenue")
    return figure.to_plotly_json()

from datetime import datetime, timezone
from fpdf import FPDF
from backend.models import FinancialMetrics


def _section(pdf: FPDF, title: str) -> None:
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(230, 245, 240)
    pdf.set_text_color(10, 40, 30)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(20, 20, 20)
    pdf.ln(1)


def build_pdf(filename: str, metrics: FinancialMetrics, risk: dict, revenue: dict, sentiment: dict,
              recommendation: dict, health: float) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "FinSight AI - Investment Analysis Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, f"Report: {filename}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    _section(pdf, "Financial Health Score")
    pdf.multi_cell(0, 7, f"{health:.0f} / 100")
    pdf.ln(2)

    _section(pdf, "Key Metrics (preliminary extraction)")
    for label, value in [("Revenue", metrics.revenue), ("Net income", metrics.net_income),
                          ("Total assets", metrics.assets), ("Total liabilities", metrics.liabilities),
                          ("Operating cash flow", metrics.operating_cash_flow)]:
        pdf.cell(0, 7, f"{label}: ${value:,.0f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    _section(pdf, "Risk Analysis")
    pdf.multi_cell(0, 7, f"Risk score: {risk['risk_score']} / 100 ({risk['risk_level']} risk)\n"
                          f"Debt ratio: {risk['debt_ratio']:.1%}\n"
                          f"Revenue growth: {risk['revenue_growth_pct']:.1f}%\n\n{risk['explanation']}")
    pdf.ln(2)

    _section(pdf, "Revenue Forecast")
    forecast_line = ", ".join(f"${v:,.0f}" for v in revenue["forecast"])
    pdf.multi_cell(0, 7, f"Latest revenue: ${revenue['latest_revenue']:,.0f}\n"
                          f"Trend: {revenue['trend']}\n"
                          f"Forecast (next {len(revenue['forecast'])} periods): {forecast_line}\n"
                          f"{revenue['growth_opportunity']}")
    pdf.ln(2)

    _section(pdf, "Market Sentiment")
    pdf.multi_cell(0, 7, f"Sentiment: {sentiment['sentiment']} ({sentiment['confidence']:.0%} confidence)")
    pdf.ln(2)

    _section(pdf, "Investment Recommendation")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, recommendation["recommendation"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, f"Investment score: {recommendation['investment_score']} / 100\n\n{recommendation['reasoning']}")
    pdf.ln(6)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, "FinSight AI is an analytical aid, not financial advice. Financial metrics are "
                          "extracted heuristically from the uploaded PDF and may be incomplete.")

    return bytes(pdf.output())

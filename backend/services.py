import re
from datetime import datetime
from backend.models import FinancialMetrics

_NUMBER = re.compile(r"[\d][\d,]*(?:\.\d+)?")


def _numbers_after(text: str, label_pattern: str, count: int, min_magnitude: float = 100) -> list[float]:
    """Find `count` comparative-year figures right after a statement label.

    10-Ks repeat the same label in a segment/product table with a "% Change" column
    interleaved between the dollar figures (e.g. "$416,161  6% $391,035  2% $383,285").
    Those stray 1-2 digit change percentages are far smaller than any real reported total,
    so a window that hits one before collecting `count` figures is rejected in favor of the
    next occurrence of the label in the document (normally the clean primary statement).
    """
    for match in re.finditer(label_pattern, text, flags=re.IGNORECASE):
        window = text[match.end(): match.end() + 250]
        values: list[float] = []
        for token in _NUMBER.findall(window):
            value = float(token.replace(",", ""))
            if value < min_magnitude:
                break
            values.append(value)
            if len(values) == count:
                return values
    return []


def extract_revenue_history(text: str) -> list[float]:
    """Chronological (oldest-to-newest) revenue for the fiscal years shown in the primary
    income statement, when the filing reports the usual 3-year comparison."""
    values = _numbers_after(text, r"total\s+net\s+sales", count=3) or _numbers_after(text, r"total\s+revenues?", count=3)
    return list(reversed(values))


def extract_latest_fiscal_year(text: str) -> int | None:
    match = re.search(r"fiscal\s+year\s+ended\s+\w+[\s\xa0]+\d{1,2},\s*(\d{4})", text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def extract_metrics(text: str) -> FinancialMetrics:
    """Best-effort extraction; displayed metrics are explicitly preliminary.

    Patterns are tried in order per field (most specific first) so a labeled total in the
    primary financial statements is preferred over a same-named figure buried in a segment
    table, footnote, or unrelated disclosure (e.g. a stock par-value amount).
    """
    patterns = {
        "revenue": [r"total\s+net\s+sales.{0,40}?\$?\s*([\d][\d,]*(?:\.\d+)?)",
                    r"total\s+revenues?.{0,40}?\$?\s*([\d][\d,]*(?:\.\d+)?)",
                    r"(?:net\s+sales|net\s+revenue|revenue).{0,40}?\$?\s*([\d][\d,]*(?:\.\d+)?)"],
        "net_income": [r"net\s+income.{0,40}?\$?\s*([\d][\d,]*(?:\.\d+)?)"],
        "assets": [r"total\s+assets.{0,40}?\$?\s*([\d][\d,]*(?:\.\d+)?)"],
        "liabilities": [r"total\s+liabilities(?!\s+and).{0,40}?\$?\s*([\d][\d,]*(?:\.\d+)?)"],
        "operating_cash_flow": [r"(?<!to\s)(?:cash\s+generated\s+by\s+operating\s+activities|"
                                 r"net\s+cash\s+provided\s+by\s+operating\s+activities|"
                                 r"cash\s+flow\s+from\s+operations|operating\s+cash\s+flow)"
                                 r".{0,40}?\$?\s*([\d][\d,]*(?:\.\d+)?)"],
    }
    values = {}
    for field, field_patterns in patterns.items():
        values[field] = 0
        for pattern in field_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            raw_value = match.group(1).replace(",", "").strip()
            try:
                values[field] = float(raw_value) if raw_value else 0
            except ValueError:
                values[field] = 0
            break
    values["revenue_history"] = extract_revenue_history(text)
    return FinancialMetrics(**values)


def health_score(metrics: FinancialMetrics) -> float:
    debt = metrics.liabilities / metrics.assets if metrics.assets else .5
    profit_margin = metrics.net_income / metrics.revenue if metrics.revenue else 0
    cash_quality = metrics.operating_cash_flow / metrics.net_income if metrics.net_income else 0
    return round(max(0, min(100, 65 - debt * 25 + profit_margin * 100 + min(15, cash_quality * 10))), 1)

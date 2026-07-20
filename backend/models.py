from pydantic import BaseModel, Field


class FinancialMetrics(BaseModel):
    revenue: float = 0
    net_income: float = 0
    assets: float = 0
    liabilities: float = 0
    operating_cash_flow: float = 0
    revenue_history: list[float] = Field(default_factory=list)


class Source(BaseModel):
    page: int
    excerpt: str


class ChatRequest(BaseModel):
    report_id: str
    question: str = Field(min_length=3, max_length=2000)


class SentimentRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=30)


class CompetitorRequest(BaseModel):
    companies: dict[str, FinancialMetrics] = Field(min_length=2, max_length=6)


class RecommendationRequest(BaseModel):
    metrics: FinancialMetrics
    sentiment_texts: list[str] = Field(default_factory=lambda: ["neutral market coverage"], max_length=30)
    latest_year: int | None = None

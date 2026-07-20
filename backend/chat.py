from langchain_core.messages import HumanMessage, SystemMessage
from backend.config import settings
from backend.rag.retriever import retrieve


def answer_question(report_id: str, question: str) -> dict:
    context, sources = retrieve(report_id, question)
    fallback = "I found these relevant report excerpts. Configure GROQ_API_KEY for a generated answer."
    if settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model, temperature=0)
            response = llm.invoke([SystemMessage(content="Answer only from supplied annual-report context. State uncertainty.\n" + context), HumanMessage(content=question)])
            answer = response.content if isinstance(response.content, str) else str(response.content)
        except Exception:
            answer = fallback
    else:
        answer = fallback
    return {"answer": answer, "sources": [source.model_dump() for source in sources]}

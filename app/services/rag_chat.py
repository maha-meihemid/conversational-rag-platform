from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from app.core.config import settings
from app.rag.vector_store import create_embeddings, create_vector_store, search_documents

SearchFunction = Callable[[str, int], list[tuple[Document, float]]]
GenerateFunction = Callable[[list[BaseMessage]], BaseMessage]

NO_ANSWER = "I do not have enough information in the banking knowledge base to answer that."

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a reliable banking FAQ assistant. Answer the user's question using only "
            "the supplied context. Do not invent policies, fees, limits, or procedures. "
            "Answer clearly and concisely in the same language as the user. If the context "
            "does not contain the answer, say that you do not have enough information.",
        ),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "Question:\n{question}\n\nContext:\n{context}"),
    ]
)

REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Rewrite the latest user question as a standalone search question using the "
            "conversation history. Keep the same language. Return only the rewritten "
            "question and do not answer it.",
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "Latest question: {question}"),
    ]
)


@dataclass(frozen=True)
class Source:
    faq_id: str
    category: str
    question: str
    score: float


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    sources: list[Source]


class RAGChatService:
    def __init__(
        self,
        search: SearchFunction,
        generate: GenerateFunction,
        *,
        top_k: int = 5,
        min_score: float = 0.35,
        history_limit: int = 10,
    ) -> None:
        self.search = search
        self.generate = generate
        self.top_k = top_k
        self.min_score = min_score
        self.history_limit = history_limit

    def ask(self, question: str, *, history: list[BaseMessage] | None = None) -> RAGAnswer:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Question cannot be empty.")

        recent_history = (history or [])[-self.history_limit :]
        search_question = self._rewrite_question(clean_question, recent_history)
        matches = self.search(search_question, self.top_k)
        relevant_matches = [match for match in matches if match[1] >= self.min_score]

        if not relevant_matches:
            return RAGAnswer(answer=NO_ANSWER, sources=[])

        context = self._format_context(relevant_matches)
        messages = PROMPT.format_messages(
            history=recent_history,
            question=clean_question,
            context=context,
        )
        response = self.generate(messages)

        answer = self._message_text(response, "Groq returned an empty text response.")

        sources = [
            Source(
                faq_id=str(document.metadata["faq_id"]),
                category=str(document.metadata["category"]),
                question=str(document.metadata["question"]),
                score=round(score, 3),
            )
            for document, score in relevant_matches
        ]
        return RAGAnswer(answer=answer, sources=sources)

    def _rewrite_question(self, question: str, history: list[BaseMessage]) -> str:
        if not history:
            return question

        messages = REWRITE_PROMPT.format_messages(history=history, question=question)
        response = self.generate(messages)
        return self._message_text(response, "Groq returned an empty rewritten question.")

    @staticmethod
    def _message_text(message: BaseMessage, error_message: str) -> str:
        if not isinstance(message.content, str) or not message.content.strip():
            raise RuntimeError(error_message)
        return message.content.strip()

    @staticmethod
    def _format_context(matches: list[tuple[Document, float]]) -> str:
        sections = []
        for position, (document, _) in enumerate(matches, start=1):
            sections.append(f"[FAQ {position}]\n{document.page_content}")
        return "\n\n".join(sections)


def create_rag_chat_service() -> RAGChatService:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")

    vector_store = create_vector_store(create_embeddings())
    chat_model = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        reasoning_format="hidden",
        timeout=30,
        max_retries=2,
    )

    def search(query: str, top_k: int) -> list[tuple[Document, float]]:
        return search_documents(vector_store, query, top_k=top_k)

    def generate(messages: list[BaseMessage]) -> BaseMessage:
        return chat_model.invoke(messages)

    return RAGChatService(
        search=search,
        generate=generate,
        top_k=settings.retrieval_top_k,
        min_score=settings.retrieval_min_score,
        history_limit=settings.conversation_history_limit,
    )

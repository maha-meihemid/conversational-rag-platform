from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from langchain_community.chat_message_histories.sql import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.core.config import settings
from app.services.rag_chat import RAGChatService, create_rag_chat_service

HistoryFactory = Callable[[str], BaseChatMessageHistory]


class ConversationService:
    def __init__(self, rag_service: RAGChatService, history_factory: HistoryFactory) -> None:
        self.rag_service = rag_service
        self.history_factory = history_factory
        self.chain = RunnableWithMessageHistory(
            RunnableLambda(self._answer),
            history_factory,
            input_messages_key="question",
            history_messages_key="history",
        )

    def ask(self, question: str, conversation_id: str) -> str:
        clean_question = question.strip()
        clean_conversation_id = conversation_id.strip()
        if not clean_question:
            raise ValueError("Question cannot be empty.")
        if not clean_conversation_id:
            raise ValueError("Conversation ID cannot be empty.")

        response = self.chain.invoke(
            {"question": clean_question},
            config={"configurable": {"session_id": clean_conversation_id}},
        )
        if not isinstance(response, BaseMessage):
            raise RuntimeError("The conversation chain returned an invalid response.")
        return self._message_text(response)

    def clear(self, conversation_id: str) -> None:
        clean_conversation_id = conversation_id.strip()
        if not clean_conversation_id:
            raise ValueError("Conversation ID cannot be empty.")
        self.history_factory(clean_conversation_id).clear()

    def _answer(self, inputs: dict[str, Any]) -> AIMessage:
        question = str(inputs["question"])
        history = cast(list[BaseMessage], inputs.get("history", []))
        result = self.rag_service.ask(question, history=history)
        return AIMessage(content=result.answer)

    @staticmethod
    def _message_text(message: BaseMessage) -> str:
        if not isinstance(message.content, str) or not message.content.strip():
            raise RuntimeError("The conversation chain returned an empty response.")
        return message.content.strip()


def create_conversation_service() -> ConversationService:
    def get_history(conversation_id: str) -> BaseChatMessageHistory:
        return SQLChatMessageHistory(
            session_id=conversation_id,
            connection=settings.conversation_db_url,
        )

    return ConversationService(create_rag_chat_service(), get_history)

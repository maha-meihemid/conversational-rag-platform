from functools import lru_cache

from app.services.conversation import ConversationService, create_conversation_service


@lru_cache
def get_conversation_service() -> ConversationService:
    return create_conversation_service()

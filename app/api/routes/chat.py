import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import (
    APIKeyDependency,
    ChatRateLimitDependency,
    get_conversation_service,
)
from app.models.chat import ChatRequest, ChatResponse
from app.services.conversation import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])
ConversationServiceDependency = Annotated[
    ConversationService,
    Depends(get_conversation_service),
]


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    service: ConversationServiceDependency,
    _: ChatRateLimitDependency,
) -> ChatResponse:
    conversation_id = request.conversation_id or uuid4()

    try:
        answer = service.ask(request.message, str(conversation_id))
    except Exception as error:
        logger.exception("Chat request failed", extra={"conversation_id": str(conversation_id)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The chat service is temporarily unavailable.",
        ) from error

    return ChatResponse(conversation_id=conversation_id, answer=answer)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def clear_conversation(
    conversation_id: UUID,
    service: ConversationServiceDependency,
    _: APIKeyDependency,
) -> Response:
    try:
        service.clear(str(conversation_id))
    except Exception as error:
        logger.exception(
            "Conversation deletion failed",
            extra={"conversation_id": str(conversation_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The chat service is temporarily unavailable.",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    conversation_id: UUID | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        clean_value = value.strip()
        if not clean_value:
            raise ValueError("Message cannot be empty.")
        return clean_value


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str

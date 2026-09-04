from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssistantProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(default="Knowledge Assistant", min_length=1, max_length=80)
    role: str = Field(
        default="a helpful knowledge-base assistant",
        min_length=1,
        max_length=200,
    )
    domain: str = Field(default="the configured knowledge base", min_length=1, max_length=200)
    tone: str = Field(default="clear, concise, and professional", min_length=1, max_length=100)
    language: str = Field(default="the same language as the user", min_length=1, max_length=100)
    instructions: str = Field(
        default="Prefer direct answers and practical steps when the context provides them.",
        max_length=2_000,
    )
    fallback_message: str = Field(
        default="I do not have enough information in the knowledge base to answer that.",
        min_length=1,
        max_length=300,
    )

    @field_validator(
        "name",
        "role",
        "domain",
        "tone",
        "language",
        "instructions",
        "fallback_message",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


DEFAULT_ASSISTANT_PROFILE = AssistantProfile()

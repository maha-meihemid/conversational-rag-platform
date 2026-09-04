from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.models.assistant import AssistantProfile


class AssistantProfileStore:
    def __init__(self, path: Path, default_profile: AssistantProfile) -> None:
        self.path = path
        self.default_profile = default_profile

    def get(self) -> AssistantProfile:
        if not self.path.is_file():
            return self.default_profile
        return AssistantProfile.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, profile: AssistantProfile) -> AssistantProfile:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary_path.write_text(profile.model_dump_json(indent=2) + "\n", encoding="utf-8")
        temporary_path.replace(self.path)
        return profile


@lru_cache
def get_assistant_profile_store() -> AssistantProfileStore:
    default_profile = AssistantProfile(
        name=settings.assistant_name,
        role=settings.assistant_role,
        domain=settings.assistant_domain,
        tone=settings.assistant_tone,
        language=settings.assistant_language,
        instructions=settings.assistant_instructions,
        fallback_message=settings.assistant_fallback_message,
    )
    return AssistantProfileStore(Path(settings.assistant_profile_path), default_profile)

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import APIKeyDependency
from app.core.config import settings
from app.models.assistant import AssistantProfile
from app.services.assistant_profile import AssistantProfileStore, get_assistant_profile_store

router = APIRouter(prefix="/assistant-profile", tags=["assistant configuration"])
ProfileStoreDependency = Annotated[
    AssistantProfileStore,
    Depends(get_assistant_profile_store),
]


@router.get("", response_model=AssistantProfile)
def read_assistant_profile(store: ProfileStoreDependency) -> AssistantProfile:
    return store.get()


@router.put("", response_model=AssistantProfile)
def update_assistant_profile(
    profile: AssistantProfile,
    store: ProfileStoreDependency,
    _: APIKeyDependency,
) -> AssistantProfile:
    if not settings.assistant_profile_editing_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assistant profile editing is disabled.",
        )
    return store.save(profile)

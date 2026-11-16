from fastapi import APIRouter

from app.core.dependencies import APIKeyPrincipal

router = APIRouter(prefix="/protected", tags=["API Key Authentication"])


@router.get("/resource", summary="Example endpoint authenticated by an API key")
async def protected_resource(api_key: APIKeyPrincipal) -> dict[str, str]:
    return {"message": "API key accepted", "api_key_id": str(api_key.id)}

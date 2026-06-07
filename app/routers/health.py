import os
from fastapi import APIRouter

router = APIRouter(tags=["health"])

LIBELULA_APPKEY = os.getenv("LIBELULA_APPKEY")
LIBELULA_API_URL = os.getenv("LIBELULA_API_URL", "https://api.libelula.bo")


@router.get("/health")
def health():
    return {
        "status": "ok",
        "libelula_appkey_configured": LIBELULA_APPKEY is not None,
        "libelula_api_url": LIBELULA_API_URL,
    }

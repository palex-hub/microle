import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Proyecto

router = APIRouter(tags=["callback"])


@router.get("/callback/{proyecto_id}")
async def recibir_callback(
    proyecto_id: int,
    transaction_id: str = Query(...),
    db: Session = Depends(get_db),
):
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto or not proyecto.callback_url:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado o sin callback_url")

    forward_url = f"{proyecto.callback_url}?transaction_id={transaction_id}"

    async with httpx.AsyncClient() as client:
        try:
            await client.get(forward_url, timeout=30)
        except Exception:
            pass

    return {"status": "ok"}

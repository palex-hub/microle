import os
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Proyecto, Pago
from app.schemas import RegistrarDeudaRequest, ConsultaDeudaRequest

router = APIRouter(prefix="/api/libelula/deuda", tags=["deuda"])

LIBELULA_APPKEY = os.getenv("LIBELULA_APPKEY")
LIBELULA_API_URL = os.getenv("LIBELULA_API_URL", "https://api.libelula.bo")
SELF_URL = os.getenv("SELF_URL")


@router.post("/consulta_deuda")
async def consulta_deuda(data: ConsultaDeudaRequest):
    if not LIBELULA_APPKEY:
        raise HTTPException(status_code=500, detail="LIBELULA_APPKEY no configurado")

    payload = {
        "appkey": LIBELULA_APPKEY,
        "identificador": data.identificador,
    }

    url = f"{LIBELULA_API_URL}/rest/deuda/consultar_deudas/por_identificador"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=60)

    result = response.json()

    if result.get("error") != 0:
        raise HTTPException(status_code=400, detail=result.get("mensaje", "Error al consultar deuda"))

    datos = result.get("datos", {})
    return {
        "identificador": datos.get("identificador"),
        "email_cliente": datos.get("email_cliente"),
        "url_pasarela_pagos": datos.get("url_pasarela_pagos"),
    }


@router.post("/registrar")
async def registrar_deuda(
    data: RegistrarDeudaRequest,
    db: Session = Depends(get_db),
):
    if not LIBELULA_APPKEY:
        raise HTTPException(status_code=500, detail="LIBELULA_APPKEY no configurado")

    proyecto = db.query(Proyecto).filter(
        Proyecto.api_key == data.api_key,
        Proyecto.activo == True,
    ).first()
    if not proyecto:
        raise HTTPException(
            status_code=401,
            detail="API Key inválida o proyecto inactivo",
        )

    ahora = datetime.now(timezone.utc)

    pago_vencido = db.query(Pago).filter(
        Pago.proyecto_id == proyecto.id,
        Pago.fecha_fin.isnot(None),
        Pago.fecha_fin < ahora,
    ).first()

    if pago_vencido:
        proyecto.activo = False
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="Proyecto desactivado por fecha de vencimiento de pago",
        )

    payload = data.model_dump(exclude_none=True)
    payload.pop("api_key", None)
    payload.pop("callback_url", None)
    payload.pop("url_retorno", None)
    payload["appkey"] = LIBELULA_APPKEY
    payload["callback_url"] = f"{SELF_URL}/callback/{proyecto.id}" if SELF_URL else None
    if proyecto.retorno_url:
        payload["url_retorno"] = proyecto.retorno_url

    for linea in payload.get("lineas_detalle_deuda", []):
        if linea.get("costo_unitario", 0) > 0:
            linea["costo_unitario"] = 0.10

    url = f"{LIBELULA_API_URL}/rest/deuda/registrar"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=60)

    return response.json()

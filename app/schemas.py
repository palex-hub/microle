from typing import Optional, List
from pydantic import BaseModel


class LineaDetalleDeuda(BaseModel):
    concepto: str
    cantidad: int
    costo_unitario: float
    descuento_unitario: Optional[float] = None
    codigo_producto: Optional[str] = None


class RegistrarDeudaRequest(BaseModel):
    email_cliente: str
    identificador: str
    lineas_detalle_deuda: List[LineaDetalleDeuda]
    callback_url: Optional[str] = None
    url_retorno: Optional[str] = None
    nombre_cliente: Optional[str] = None
    apellido_cliente: Optional[str] = None
    descripcion: Optional[str] = None
    api_key: str


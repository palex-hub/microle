from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    registro = Column(DateTime(timezone=True), server_default=func.now())

    proyectos = relationship("Proyecto", back_populates="usuario")


class Proyecto(Base):
    __tablename__ = "proyecto"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    callback_url = Column(String(500), unique=True, nullable=True)
    retorno_url = Column(String(500), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    activo = Column(Boolean, default=True)

    usuario = relationship("Usuario", back_populates="proyectos")
    pagos = relationship("Pago", back_populates="proyecto")


class Pago(Base):
    __tablename__ = "pago"

    id = Column(Integer, primary_key=True, index=True)
    fecha_inicio = Column(DateTime(timezone=True))
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    monto = Column(Numeric(10, 2), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"), nullable=False)

    proyecto = relationship("Proyecto", back_populates="pagos")

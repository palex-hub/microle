import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.routers import health, deuda, callback

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Libélula Cuartiario",
    description="Microservicio cuartiario para pasarela de pagos Libélula",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(deuda.router)
app.include_router(callback.router)

debug = os.getenv("STAGE", "dev") == "dev"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {request.method} {request.url.path}: {exc}", flush=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if debug else "Error interno del servidor"},
    )


@app.get("/")
async def root():
    return {"message": "Libélula Cuartiario - Serverless"}

from fastapi import FastAPI
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


@app.get("/")
async def root():
    return {"message": "Libélula Cuartiario - Serverless"}

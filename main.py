from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WeldFOAM API",
    description="Калькулятор сварочных деформаций и напряжений по методу Окерблома",
    version="0.1.0"
)

# CORS для Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров (у него уже есть prefix="/api/v1")
app.include_router(router)

@app.get("/")
async def root():
    # Пути из роутера уже содержат /api/v1, не добавляем повторно
    paths = [route.path for route in router.routes]
    return {
        "service": "WeldFOAM",
        "version": "0.1.0",
        "endpoints": sorted(paths)
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "WeldFOAM"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
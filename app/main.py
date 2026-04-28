from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.pages import router as pages_router
from app.routes.analysis import router as analysis_router

app = FastAPI(title="TechDebt Analyzer")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages_router)
app.include_router(analysis_router)

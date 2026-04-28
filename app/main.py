from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from app.routes import pages, analysis

app = FastAPI()

# Initialize state so it never throws AttributeError
app.state.last_result     = None
app.state.analysis_status = "idle"

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

app.include_router(pages.router)
app.include_router(analysis.router)
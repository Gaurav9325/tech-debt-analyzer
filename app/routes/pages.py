from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html")


@router.get("/analyzer")
def analyzer(request: Request):
    return templates.TemplateResponse(request, "index.html")

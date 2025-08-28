"""
主API路由
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="webapp/templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """返回主页 - Legacy版本"""
    return templates.TemplateResponse("index_legacy.html", {"request": request})


@router.get("/material", response_class=HTMLResponse)
async def read_material(request: Request):
    """返回Material Design界面"""
    return templates.TemplateResponse("index.html", {"request": request})

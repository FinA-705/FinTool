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
    """返回主页"""
    return templates.TemplateResponse("index.html", {"request": request})

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.storage.profile_store import load_profile

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile/{file_id}", response_class=HTMLResponse)
def profile_page(request: Request, file_id: str):
    profile = load_profile(file_id)
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "file_id": file_id,
            "profile": profile,
        },
    )

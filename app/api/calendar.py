from datetime import date, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.storage.profile_store import load_profile, save_profile
from app.core.scoring import score_day  # 我们马上创建

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/calendar/{file_id}", response_class=HTMLResponse)
def calendar_page(request: Request, file_id: str):
    profile = load_profile(file_id)
    tz = profile.get("calendar_tz", "UTC")

    start = date.today()  # v0: 先用本机日期；下一步会改成 timezone-aware
    days = []
    for i in range(30):
        d = start + timedelta(days=i)
        out = score_day(profile["parsed"], d)  # deterministic
        days.append(out)

    # 保存一份，之后 day detail 直接读取
    profile["calendar_30d"] = days
    save_profile(file_id, profile)

    return templates.TemplateResponse(
        "calendar.html",
        {"request": request, "file_id": file_id, "tz": tz, "days": days},
    )

@router.get("/day/{file_id}/{yyyy_mm_dd}", response_class=HTMLResponse)
def day_page(request: Request, file_id: str, yyyy_mm_dd: str):
    profile = load_profile(file_id)
    days = profile.get("calendar_30d", [])

    target = None
    for x in days:
        if x["date"] == yyyy_mm_dd:
            target = x
            break

    if target is None:
        # 如果用户没先生成日历，就给个提示页（先简化）
        return HTMLResponse("No calendar generated. Go to /calendar/{file_id} first.")

    return templates.TemplateResponse(
        "day.html",
        {"request": request, "file_id": file_id, "day": target},
    )

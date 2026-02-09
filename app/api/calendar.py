from datetime import date, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.storage.profile_store import load_profile, save_profile
from app.core.scoring import score_day

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _inject_deltas(days: list[dict]) -> None:
    if not days:
        return
    dim_keys = ["emotion", "wealth", "career", "social", "vitality"]
    for i, d in enumerate(days):
        scores = d.setdefault("scores", {})
        dims = scores.get("dimensions", {}) or {}
        deltas = {}
        if i == 0:
            for k in dim_keys:
                deltas[k] = 0
        else:
            prev_dims = (days[i - 1].get("scores", {}).get("dimensions", {}) or {})
            for k in dim_keys:
                cur = int(dims.get(k, 0))
                prev = int(prev_dims.get(k, 0))
                deltas[k] = cur - prev
        scores["deltas"] = deltas


@router.get("/calendar/{file_id}", response_class=HTMLResponse)
def calendar_page(request: Request, file_id: str):
    profile = load_profile(file_id)
    tz = profile.get("calendar_tz", "UTC")

    start = date.today()
    days = []
    for i in range(30):
        d = start + timedelta(days=i)
        out = score_day(profile["parsed"], d)
        days.append(out)
    _inject_deltas(days)

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
    _inject_deltas(days)

    target = None
    for x in days:
        if x["date"] == yyyy_mm_dd:
            target = x
            break

    if target is None:
        return HTMLResponse("No calendar generated. Go to /calendar/{file_id} first.")

    return templates.TemplateResponse(
        "day.html",
        {"request": request, "file_id": file_id, "day": target},
    )


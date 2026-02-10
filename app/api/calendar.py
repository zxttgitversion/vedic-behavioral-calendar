from datetime import date, timedelta, datetime
import calendar as pycal
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.storage.profile_store import load_profile, save_profile
from app.core.scoring import score_day

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


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
    # generate scores for the current month
    today = date.today()
    year = today.year
    month = today.month

    _, days_in_month = pycal.monthrange(year, month)
    days = []
    for daynum in range(1, days_in_month + 1):
        d = date(year, month, daynum)
        out = score_day(profile["parsed"], d)
        days.append(out)

    _inject_deltas(days)

    # keep a flat list for compatibility with /day route
    profile["calendar_30d"] = days
    save_profile(file_id, profile)

    # compute today in user's timezone
    today_str = date.today().isoformat()
    try:
        if ZoneInfo is not None:
            tzinfo = ZoneInfo(tz)
            today_dt = datetime.now(tzinfo)
            today_str = today_dt.date().isoformat()
    except Exception:
        # fallback to server local date
        today_str = date.today().isoformat()

    # build week grid (Monday=0 .. Sunday=6)
    first_weekday, _ = pycal.monthrange(year, month)
    weeks = []
    week = [None] * 7
    day_index = 1

    # fill first week
    for pos in range(first_weekday, 7):
        week[pos] = days[day_index - 1]
        day_index += 1
        if day_index > days_in_month:
            break
    weeks.append(week)

    # fill remaining weeks
    while day_index <= days_in_month:
        week = []
        for pos in range(7):
            if day_index <= days_in_month:
                week.append(days[day_index - 1])
                day_index += 1
            else:
                week.append(None)
        weeks.append(week)

    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "file_id": file_id,
            "tz": tz,
            "weeks": weeks,
            "year": year,
            "month": month,
            "weekday_names": weekday_names,
            "today_str": today_str,
        },
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


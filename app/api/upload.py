from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.jh_report_parser import parse_report_text

from fastapi.responses import RedirectResponse
from app.storage.profile_store import save_profile


router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Mapping of IANA timezone IDs to user-friendly names with UTC offset
TIMEZONE_DISPLAY_MAP = {
    "UTC": "UTC (UTC+0:00)",
    "Europe/London": "London (UTC+0:00 / UTC+1:00)",
    "Europe/Paris": "Paris (UTC+1:00 / UTC+2:00)",
    "Asia/Shanghai": "Beijing (UTC+8:00)",
    "Asia/Hong_Kong": "Hong Kong (UTC+8:00)",
    "Asia/Tokyo": "Tokyo (UTC+9:00)",
    "US/Eastern": "New York (UTC-5:00 / UTC-4:00)",
    "US/Central": "Chicago (UTC-6:00 / UTC-5:00)",
    "US/Mountain": "Denver (UTC-7:00 / UTC-6:00)",
    "US/Pacific": "Los Angeles (UTC-8:00 / UTC-7:00)",
}

def format_utc_offset(minutes: int) -> str:
    """Convert UTC offset in minutes to human-readable format (UTC±HH:mm)"""
    if minutes == 0:
        return "UTC±0:00"
    sign = "+" if minutes > 0 else "-"
    hours = abs(minutes) // 60
    mins = abs(minutes) % 60
    return f"UTC{sign}{hours:02d}:{mins:02d}"

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    calendar_tz: str = "auto",
    device_tz: str = "UTC"
):
    file_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix or ".txt"
    save_path = UPLOAD_DIR / f"{file_id}{suffix}"

    content = await file.read()
    save_path.write_bytes(content)

    # 1) calendar timezone：auto → device/user provided later (v1.0 now default London if auto)
    # calendar_tz: auto -> use device_tz
    if calendar_tz == "auto":
        calendar_tz = device_tz or "UTC"

    # 2) 按“用户选择时区”的今天来判定当前 dasha
    try:
        tz = ZoneInfo(calendar_tz)
    except Exception:
        tz = ZoneInfo("UTC")

    today = datetime.now(tz).date()




    # 3) 解析文本
    text = content.decode("utf-8", errors="replace")

    


    # parsed = parse_report_text(text, today)
    try:
        parsed = parse_report_text(text, today)
    except Exception as e:
        return {
            "file_id": file_id,
            "calendar_tz": calendar_tz,
            "error": str(e)
        }


    save_profile(
        file_id,
        {
            "calendar_tz": calendar_tz,
            "parsed": {
                "birth_date": parsed.birth_date,
                "birth_time": parsed.birth_time,
                "natal_nakshatra_name": parsed.natal_nakshatra_name,
                "birth_utc_offset_minutes": parsed.birth_utc_offset_minutes,
                "birth_utc_offset_display": format_utc_offset(parsed.birth_utc_offset_minutes),
                "dasha_maha": parsed.dasha_maha,
                "dasha_antar": parsed.dasha_antar,
                "lagna_rasi": parsed.lagna_rasi,
                "natal_moon_rasi": parsed.natal_moon_rasi,

                # ✅ NEW: for v1.1 base engine explainability
                "dasha_maha_house": parsed.dasha_maha_house,
                "dasha_antar_house": parsed.dasha_antar_house,

                # (optional but recommended)
                "planet_rasi": parsed.planet_rasi,
                "planet_houses": parsed.planet_houses,
                "bav_rasi": parsed.bav_rasi,
                },


        },
    )

    return RedirectResponse(
        url=f"/profile/{file_id}",
        status_code=303,
    )


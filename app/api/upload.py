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
                "natal_nakshatra_name": parsed.natal_nakshatra_name,
                "birth_utc_offset_minutes": parsed.birth_utc_offset_minutes,
                "dasha_maha": parsed.dasha_maha,
                "dasha_antar": parsed.dasha_antar,
                "lagna_rasi": parsed.lagna_rasi,  # ✅ ADD THIS
            },

        },
    )

    return RedirectResponse(
        url=f"/profile/{file_id}",
        status_code=303,
    )


# app/core/daily_features.py
from datetime import date
from typing import Dict, Any
from app.core.constants import NAK_ORDER, RASI_ORDER

def get_daily_features_stub(d: date, natal_nak: str) -> Dict[str, Any]:
    """
    Deterministic stub for v1.1 integration.
    Replace with Swiss Ephemeris in v1.2.
    """
    # nak cycles every day
    transit_nak = NAK_ORDER[d.toordinal() % 27]
    # moon rasi cycles every 2 days
    moon_rasi = RASI_ORDER[(d.toordinal() // 2) % 12]
    # tithi cycles 1..30
    tithi = (d.toordinal() % 30) + 1
    return {
        "transit_nakshatra": transit_nak,
        "moon_rasi": moon_rasi,
        "tithi": tithi,
    }

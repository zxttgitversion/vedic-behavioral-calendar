# app/core/daily_features.py
from datetime import date
from typing import Dict, Any
from app.core.constants import NAK_ORDER, RASI_ORDER

# def get_daily_features_stub(d: date, natal_nak: str) -> Dict[str, Any]:
#     """
#     Deterministic stub for v1.1 integration.
#     Replace with Swiss Ephemeris in v1.2.
#     """
#     # nak cycles every day
#     transit_nak = NAK_ORDER[d.toordinal() % 27]
#     # moon rasi cycles every 2 days
#     moon_rasi = RASI_ORDER[(d.toordinal() // 2) % 12]
#     # tithi cycles 1..30
#     tithi = (d.toordinal() % 30) + 1
#     return {
#         "transit_nakshatra": transit_nak,
#         "moon_rasi": moon_rasi,
#         "tithi": tithi,
#     }

def get_daily_features_swe(d: date, natal_nak: str) -> Dict[str, Any]:
    """
    Swiss Ephemeris-backed daily features for v1.3.
    Deterministic: use 12:00 UTC for the given date.
    Uses MOSEPH so it doesn't require ephemeris data files.
    """
    import swisseph as swe

    # 12:00 UTC for determinism (no timezone/location yet)
    jd = swe.julday(d.year, d.month, d.day, 12.0)

    # sidereal zodiac (Lahiri) so rasi/nakshatra mapping is meaningful
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_MOSEPH

    moon_pos, _ = swe.calc_ut(jd, swe.MOON, flags)
    sun_pos, _ = swe.calc_ut(jd, swe.SUN, flags)

    moon_lon = moon_pos[0] % 360.0
    sun_lon = sun_pos[0] % 360.0

    # rasi: 12 signs, 30° each
    rasi_idx = int(moon_lon // 30.0)  # 0..11
    moon_rasi = RASI_ORDER[rasi_idx]

    # nakshatra: 27 parts, 13°20' = 13.333333...
    nak_idx = int(moon_lon // (360.0 / 27.0))  # 0..26
    transit_nak = NAK_ORDER[nak_idx]

    # tithi: based on (moon - sun) / 12° + 1, wrap 1..30
    diff = (moon_lon - sun_lon) % 360.0
    tithi = int(diff // 12.0) + 1

    planet_ids = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mars": swe.MARS,
        "Merc": swe.MERCURY,
        "Jup": swe.JUPITER,
        "Ven": swe.VENUS,
        "Sat": swe.SATURN,
    }
    planet_rasi = {}
    planet_status = {}
    for name, pid in planet_ids.items():
        pos, _ = swe.calc_ut(jd, pid, flags)
        lon = pos[0] % 360.0
        idx = int(lon // 30.0)
        planet_rasi[name] = RASI_ORDER[idx]
        speed_lon = float(pos[3]) if len(pos) > 3 else 0.0
        planet_status[name] = {"is_retrograde": speed_lon < 0.0}

    return {
        "transit_nakshatra": transit_nak,
        "moon_rasi": moon_rasi,
        "tithi": tithi,
        "planet_rasi": planet_rasi,
        "planet_status": planet_status,
    }

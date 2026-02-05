# app/core/astrology_rules.py
from datetime import date
from typing import Dict, Any, List, Tuple

from app.core.constants import RASI_ORDER, NAK_ORDER, TARA_TABLE, TARA_INDEX_TO_LABEL, TARA_9CYCLE_TO_7LABEL

FULL_TO_ABBR = {
    "Ashwini": "Aswi",
    "Bharani": "Bhar",
    "Krittika": "Krit",
    "Rohini": "Rohi",
    "Mrigashirsha": "Mrig",
    "Ardra": "Ardr",
    "Punarvasu": "Puna",
    "Pushya": "Push",
    "Ashlesha": "Asle",
    "Magha": "Magh",
    "Purva Phalguni": "PPha",
    "Uttara Phalguni": "UPha",
    "Hasta": "Hast",
    "Chitra": "Chit",
    "Swati": "Swat",
    "Vishakha": "Visa",
    "Anuradha": "Anu",
    "Jyeshtha": "Jye",
    "Mula": "Mool",
    "Purva Ashadha": "PSha",
    "Uttara Ashadha": "USha",
    "Shravana": "Srav",
    "Dhanishta": "Dhan",
    "Shatabhisha": "Sata",
    "Purva Bhadrapada": "PBha",
    "Uttara Bhadrapada": "UBha",
    "Revati": "Reva",
}



def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def rasi_to_index(rasi: str) -> int:
    # returns 0..11
    if rasi not in RASI_ORDER:
        raise ValueError(f"Unknown rasi: {rasi}")
    return RASI_ORDER.index(rasi)

def house_from_lagna_and_moon(lagna_rasi: str, moon_rasi: str) -> int:
    """
    House 1 = Lagna rasi
    House = (moon_index - lagna_index) mod 12 + 1
    """
    li = rasi_to_index(lagna_rasi)
    mi = rasi_to_index(moon_rasi)
    return ((mi - li) % 12) + 1

def nak_to_index(nak: str) -> int:
    """
    Accept both:
    - JHora abbreviations: Visa/Chit/Anu...
    - Full names: Visakha/Vishakha/Chitra/Anuradha...
    - Strings with suffix like: "Visakha (Ju)"
    """

    x = (nak or "").strip()

    # drop suffix like "(Ju)"
    if "(" in x:
        x = x.split("(")[0].strip()

    # normalize spelling variations
    x_norm = x.lower().replace(" ", "").replace("-", "")

    # 1) direct abbreviation
    if x in NAK_ORDER:
        return NAK_ORDER.index(x)

    # 2) robust full-name mapping (handle Visakha/Vishakha etc.)
    full_to_abbr_norm = {
        "ashwini": "Aswi",
        "bharani": "Bhar",
        "krittika": "Krit",
        "rohini": "Rohi",
        "mrigashirsha": "Mrig",
        "ardra": "Ardr",
        "punarvasu": "Puna",
        "pushya": "Push",
        "ashlesha": "Asle",
        "magha": "Magh",
        "purvaphalguni": "PPha",
        "uttaraphalguni": "UPha",
        "hasta": "Hast",
        "chitra": "Chit",
        "swati": "Swat",
        # ✅ handle both spellings
        "visakha": "Visa",
        "vishakha": "Visa",
        "anuradha": "Anu",
        "jyeshtha": "Jye",
        "mula": "Mool",
        "purvaashadha": "PSha",
        "uttaraashadha": "USha",
        "shravana": "Srav",
        "dhanishta": "Dhan",
        "shatabhisha": "Sata",
        "purvabhadrapada": "PBha",
        "uttarabhadrapada": "UBha",
        "revati": "Reva",
    }

    if x_norm in full_to_abbr_norm:
        abbr = full_to_abbr_norm[x_norm]
        return NAK_ORDER.index(abbr)

    raise ValueError(f"Unknown nakshatra: {nak}")


def tara_bala_label_and_score(natal_nak: str, transit_nak: str) -> Tuple[str, int]:
    """
    Standard: count from natal to transit (inclusive) => 1..27
    Tara index = ((count-1) % 9) + 1
    Map 9-cycle to our 7-label score table.
    """
    n = nak_to_index(natal_nak)
    t = nak_to_index(transit_nak)
    count = ((t - n) % 27) + 1  # 1..27 inclusive
    tara_idx = ((count - 1) % 9) + 1
    label9 = TARA_INDEX_TO_LABEL[tara_idx]
    label7 = TARA_9CYCLE_TO_7LABEL[label9]
    score = TARA_TABLE[label7]
    return label7, score

def special_flags(natal_nak: str, transit_nak: str, tithi: int) -> List[str]:
    flags = []
    if natal_nak == transit_nak:
        flags.append("janma_nakshatra")
    if tithi in (4, 9, 14):
        flags.append("rikta_tithi")
    return flags

def apply_special_day_overrides(signal: str, score: float, flags: List[str], tara_label: str) -> Tuple[str, float]:
    """
    UI rule:
    - if rikta_tithi -> signal not higher than Yellow
    - if rikta_tithi + (Vipat/Pratyari) -> force Red
    """
    # clamp score first? We'll do logic at signal layer (deterministic)
    if "rikta_tithi" in flags:
        if tara_label in ("Vipat", "Pratyari"):
            return "red", min(score, 39.0)
        # cap at yellow
        if signal == "green":
            return "yellow", min(score, 69.0)
    return signal, score

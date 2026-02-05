import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

from app.core.astrology_rules import house_from_lagna_and_moon

# Vimsottari timeline uses these abbreviations
PLANETS = {"Sun", "Moon", "Mars", "Merc", "Jup", "Ven", "Sat", "Rah", "Ket"}

# Body table uses full names; map to the abbreviations above
BODY_NAME_TO_ABBR = {
    "Sun": "Sun",
    "Moon": "Moon",
    "Mars": "Mars",
    "Mercury": "Merc",
    "Jupiter": "Jup",
    "Venus": "Ven",
    "Saturn": "Sat",
    "Rahu": "Rah",
    "Ketu": "Ket",
}


@dataclass
class ParsedProfile:
    natal_nakshatra_name: str
    birth_utc_offset_minutes: int
    dasha_maha: str
    dasha_antar: str
    lagna_rasi: Optional[str] = None

    # NEW: raw planet rasi mapping parsed from Body table
    planet_rasi: Optional[Dict[str, str]] = None

    # NEW: planet houses computed from lagna_rasi + planet_rasi
    planet_houses: Optional[Dict[str, int]] = None

    # NEW: houses for current MD/AD (if available)
    dasha_maha_house: Optional[int] = None
    dasha_antar_house: Optional[int] = None


def _parse_birth_utc_offset_minutes(text: str) -> int:
    """
    Parse: Time Zone:  8:00:00 (East of GMT)
    Return: minutes, e.g. +480
    """
    m = re.search(r"Time Zone:\s*([+-]?\d+):(\d+):(\d+)\s*\((East|West) of GMT\)", text)
    if not m:
        raise ValueError("Cannot find 'Time Zone:' line in report")

    hours = int(m.group(1))
    minutes = int(m.group(2))
    seconds = int(m.group(3))
    direction = m.group(4)

    total = abs(hours) * 60 + minutes + (1 if seconds >= 30 else 0)
    sign = +1 if direction == "East" else -1
    return sign * total


def _parse_natal_nakshatra_name(text: str) -> str:
    """
    Parse: Nakshatra:  Visakha (Ju)
    Return: 'Visakha'
    """
    m = re.search(r"^Nakshatra:\s*([A-Za-z]+)\s*\(", text, flags=re.MULTILINE)
    if not m:
        raise ValueError("Cannot find 'Nakshatra:' line in report")
    return m.group(1).strip()


def _parse_lagna_rasi(text: str) -> Optional[str]:
    """
    Parse Lagna rasi from the Body table line, e.g.
      Lagna  20 Sc 20' 42.50" ...
    Capture: 'Sc'
    """
    m = re.search(r"^Lagna\s+\d+\s+([A-Za-z]{2})\s+\d+'", text, flags=re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip()


def _parse_planet_rasi_map(text: str) -> Dict[str, str]:
    """
    Parse planet rasi from the Body table section, e.g.
      Sun - AK                24 Ar 13' ...
      Mercury - PK             9 Ta 38' ...
      Rahu                    16 Ge 15' ...

    Output keys are abbreviations used by Vimsottari timeline:
      Sun/Moon/Mars/Merc/Jup/Ven/Sat/Rah/Ket
    """
    # Match start of line: planet name, then anything (e.g., "- AK"), then degrees + rasi
    # Example: "Mercury - PK             9 Ta 38' 48.48" ..."
    planet_pattern = re.compile(
        r"^(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b.*?\s(\d+)\s+([A-Za-z]{2})\s+\d+'",
        flags=re.MULTILINE,
    )

    out: Dict[str, str] = {}
    for m in planet_pattern.finditer(text):
        full_name = m.group(1)
        rasi = m.group(3).strip()
        abbr = BODY_NAME_TO_ABBR.get(full_name)
        if abbr:
            out[abbr] = rasi

    return out


def _extract_vimsottari_block(text: str) -> str:
    """
    Extract everything between 'Vimsottari Dasa' header and next Dasa section header.
    """
    lines = text.splitlines()

    header_i = None
    for i, line in enumerate(lines):
        if "Vimsottari Dasa" in line:
            header_i = i
            break
    if header_i is None:
        raise ValueError("Cannot find 'Vimsottari Dasa' section")

    end_i = len(lines)
    for j in range(header_i + 1, len(lines)):
        s = lines[j].strip()
        if re.match(r"^(Moola Dasa|Ashtottari Dasa|Kalachakra Dasa|Narayana Dasa)\b", s):
            end_i = j
            break

    block_lines = lines[header_i + 1 : end_i]

    while block_lines and block_lines[0].strip() == "":
        block_lines.pop(0)
    while block_lines and block_lines[-1].strip() == "":
        block_lines.pop()

    block = "\n".join(block_lines).strip()
    if not block:
        raise ValueError("Empty Vimsottari block")
    return block


def parse_vimsottari_timeline(block: str) -> List[Tuple[str, str, date]]:
    """
    Parse rows like:
      Jup  Jup 1998-02-01  Sat 2000-03-20  Merc 2002-10-06
           Ket 2005-01-08  Ven 2005-12-16  Sun 2008-08-17
           Moon 2009-06-03  Mars 2010-10-06  Rah 2011-09-11
    Output: [(maha, antar, start_date), ...] sorted by start_date
    """
    items: List[Tuple[str, str, date]] = []
    current_maha: Optional[str] = None

    def is_date(s: str) -> bool:
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", s))

    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue

        tokens = line.split()

        # New maha block start: first token planet, second token planet, third token date
        if len(tokens) >= 3 and tokens[0] in PLANETS and tokens[1] in PLANETS and is_date(tokens[2]):
            current_maha = tokens[0]
            i = 1  # parse from tokens[1:]
        else:
            if current_maha is None:
                raise ValueError("Vimsottari block continuation found before any maha block")
            i = 0  # continuation line starts with antar

        # parse (antar, date) pairs
        while i + 1 < len(tokens):
            antar = tokens[i]
            dt = tokens[i + 1]
            if antar not in PLANETS or not is_date(dt):
                break
            y, mo, da = map(int, dt.split("-"))
            items.append((current_maha, antar, date(y, mo, da)))
            i += 2

    # sort & dedup
    items.sort(key=lambda x: x[2])
    deduped: List[Tuple[str, str, date]] = []
    seen = set()
    for maha, antar, dt in items:
        key = (maha, antar, dt)
        if key not in seen:
            seen.add(key)
            deduped.append(key)

    return deduped


def get_current_dasha(timeline: List[Tuple[str, str, date]], today: date) -> Tuple[str, str]:
    """
    Pick the last record whose start_date <= today.
    """
    current = None
    for maha, antar, dt in timeline:
        if dt <= today:
            current = (maha, antar, dt)
        else:
            break

    if current is None:
        maha, antar, _ = timeline[0]
        return maha, antar

    return current[0], current[1]


def parse_report_text(text: str, today: date) -> ParsedProfile:
    natal = _parse_natal_nakshatra_name(text)
    birth_offset = _parse_birth_utc_offset_minutes(text)
    lagna = _parse_lagna_rasi(text)

    vblock = _extract_vimsottari_block(text)
    timeline = parse_vimsottari_timeline(vblock)
    maha, antar = get_current_dasha(timeline, today)

    # NEW: parse planet rasi map from Body table
    planet_rasi = _parse_planet_rasi_map(text)

    # NEW: compute houses if lagna is present
    planet_houses: Optional[Dict[str, int]] = None
    maha_house: Optional[int] = None
    antar_house: Optional[int] = None
    if lagna is not None and planet_rasi:
        planet_houses = {}
        for p, rasi in planet_rasi.items():
            try:
                planet_houses[p] = house_from_lagna_and_moon(lagna, rasi)
            except Exception:
                # keep robust: skip if any unknown rasi token appears
                continue

        maha_house = planet_houses.get(maha)
        antar_house = planet_houses.get(antar)

    return ParsedProfile(
        natal_nakshatra_name=natal,
        birth_utc_offset_minutes=birth_offset,
        dasha_maha=maha,
        dasha_antar=antar,
        lagna_rasi=lagna,
        planet_rasi=planet_rasi or None,
        planet_houses=planet_houses,
        dasha_maha_house=maha_house,
        dasha_antar_house=antar_house,
    )

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
    birth_date: Optional[str] = None  # "YYYY-MM-DD" format
    birth_time: Optional[str] = None  # "HH:mm:ss" format
    lagna_rasi: Optional[str] = None
    natal_moon_rasi: Optional[str] = None

    # NEW: raw planet rasi mapping parsed from Body table
    planet_rasi: Optional[Dict[str, str]] = None

    # NEW: planet houses computed from lagna_rasi + planet_rasi
    planet_houses: Optional[Dict[str, int]] = None

    # NEW: houses for current MD/AD (if available)
    dasha_maha_house: Optional[int] = None
    dasha_antar_house: Optional[int] = None

    # NEW: BAV per planet and rasi, e.g. {"Jup": {"Ar": 5, ...}, ...}
    bav_rasi: Optional[Dict[str, Dict[str, int]]] = None


def _parse_birth_date_time(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse birth date and time from report.
    Example:
        Date:          May 7, 2001
        Time:          19:01:46
    Return: (date_str: "2001-05-07", time_str: "19:01:46") or (None, None)
    """
    from datetime import datetime as dt
    
    # Month names mapping
    month_names = {
        'January': '01', 'February': '02', 'March': '03', 'April': '04',
        'May': '05', 'June': '06', 'July': '07', 'August': '08',
        'September': '09', 'October': '10', 'November': '11', 'December': '12',
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05',
        'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10',
        'Nov': '11', 'Dec': '12'
    }
    
    date_str = None
    time_str = None
    
    # Parse Date
    date_match = re.search(r"^Date:\s*(\w+)\s+(\d+),\s*(\d{4})", text, flags=re.MULTILINE)
    if date_match:
        month_name = date_match.group(1)
        day = date_match.group(2).zfill(2)
        year = date_match.group(3)
        month = month_names.get(month_name, "01")
        date_str = f"{year}-{month}-{day}"
    
    # Parse Time
    time_match = re.search(r"^Time:\s*(\d{1,2}):(\d{2}):(\d{2})", text, flags=re.MULTILINE)
    if time_match:
        hour = time_match.group(1).zfill(2)
        minute = time_match.group(2)
        second = time_match.group(3)
        time_str = f"{hour}:{minute}:{second}"
    
    return (date_str, time_str)


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


def _parse_bav_rasi_table(text: str) -> Dict[str, Dict[str, int]]:
    """
    Parse the "Ashtakavarga of Rasi Chart" matrix.
    Example rows:
      Su   3*  2   2   4   5   5   5   2   4   6   5   5
      Ju   5   4*  5   6   5   4   4   5   5   4   5   4
    Return:
      {"Sun": {"Ar":3, ...}, "Jup": {"Ar":5, ...}, ...}
    """
    row_to_planet = {
        "Su": "Sun",
        "Mo": "Moon",
        "Ma": "Mars",
        "Me": "Merc",
        "Ju": "Jup",
        "Ve": "Ven",
        "Sa": "Sat",
    }
    sign_order = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

    lines = text.splitlines()
    start_i: Optional[int] = None
    for i, line in enumerate(lines):
        if "Ashtakavarga of Rasi Chart" in line:
            start_i = i
            break
    if start_i is None:
        return {}

    out: Dict[str, Dict[str, int]] = {}
    for line in lines[start_i + 1:]:
        s = line.strip()
        if not s:
            continue
        if s.startswith("Sodhya Pinda"):
            break

        m = re.match(r"^(Su|Mo|Ma|Me|Ju|Ve|Sa)\s+(.+)$", s)
        if not m:
            continue

        row = m.group(1)
        tail = m.group(2)
        nums = re.findall(r"\d+\*?", tail)
        if len(nums) < 12:
            continue

        scores = [int(x.replace("*", "")) for x in nums[:12]]
        out[row_to_planet[row]] = {sign_order[idx]: scores[idx] for idx in range(12)}

    return out


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
    birth_date_str, birth_time_str = _parse_birth_date_time(text)
    lagna = _parse_lagna_rasi(text)

    vblock = _extract_vimsottari_block(text)
    timeline = parse_vimsottari_timeline(vblock)
    maha, antar = get_current_dasha(timeline, today)

    # NEW: parse planet rasi map from Body table
    planet_rasi = _parse_planet_rasi_map(text)
    bav_rasi = _parse_bav_rasi_table(text)
    natal_moon_rasi = planet_rasi.get("Moon") if planet_rasi else None

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
        birth_date=birth_date_str,
        birth_time=birth_time_str,
        dasha_maha=maha,
        dasha_antar=antar,
        lagna_rasi=lagna,
        natal_moon_rasi=natal_moon_rasi,
        planet_rasi=planet_rasi or None,
        planet_houses=planet_houses,
        dasha_maha_house=maha_house,
        dasha_antar_house=antar_house,
        bav_rasi=bav_rasi or None,
    )

from typing import Any, Dict, Tuple

from app.core.constants import NAK_ORDER, RASI_ORDER, TARA_9CYCLE_TO_7LABEL, TARA_INDEX_TO_LABEL, TARA_TABLE

FULL_TO_ABBR = {
    "Ashwini": "Aswi",
    "Bharani": "Bhar",
    "Krittika": "Krit",
    "Rohini": "Rohi",
    "Mrigashirsha": "Mrig",
    "Mrigashira": "Mrig",
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
    "Visakha": "Visa",
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

I18N_LABELS: Dict[str, Any] = {
    "MODULE_TITLES": {
        "core_context": "核心星象背景 (Core Context)",
        "tara_bala": "星宿能量匹配 (Tara Bala)",
        "dimensions_drivers": "五维得分 (Score + Delta)",
    },
    "FIELD_LABELS": {
        "lagna": "上升星座 (Lagna)",
        "natal_moon_rasi": "本命月亮星座 (Chandra Lagna)",
        "dasha_relationship": "大运关系 (Dasha Relationship)",
        "natal_nakshatra": "本命星宿",
        "transit_nakshatra": "今日运行星宿",
        "tara_label": "能量性质",
    },
    "HOUSE_LABELS": {
        1: "命宫",
        2: "财帛宫",
        3: "兄弟宫",
        4: "田宅宫",
        5: "子女宫",
        6: "奴仆宫",
        7: "夫妻宫",
        8: "疾厄宫",
        9: "福德宫",
        10: "官禄宫",
        11: "愿望宫",
        12: "玄秘宫/潜意识",
    },
    "DASHA_REL_LABELS": {
        "1/1": "1/1 (同步期/资源整合)",
        "5/9": "5/9 (顺遂期/好运加持)",
        "6/8": "6/8 (磨练期/挑战与磨合)",
        "2/12": "2/12 (消耗期/积累与反思)",
        "3/11": "3/11 (成长期/机遇与进展)",
        "4/10": "4/10 (稳定期/责任与基石)",
        "7/7": "7/7 (平衡期/互动与调整)",
    },
    "DIMENSION_LABELS": {
        "emotion": {"en": "Mental Peace", "zh": "心态/宁静", "color": "#3498db"},
        "vitality": {"en": "Vitality", "zh": "体能/活力", "color": "#3498db"},
        "career": {"en": "Achievement", "zh": "事业/成就", "color": "#f1c40f"},
        "wealth": {"en": "Prosperity", "zh": "财富/资源", "color": "#f1c40f"},
        "social": {"en": "Connection", "zh": "社交/联结", "color": "#f1c40f"},
    },
    "PLANET_ZH": {
        "Sun": "太阳",
        "Moon": "月亮",
        "Mars": "火星",
        "Merc": "水星",
        "Jup": "木星",
        "Ven": "金星",
        "Sat": "土星",
        "Rah": "罗睺",
        "Ket": "计都",
    },
    "RASI_LABELS": {
        "Ar": "白羊座",
        "Ta": "金牛座",
        "Ge": "双子座",
        "Cn": "巨蟹座",
        "Le": "狮子座",
        "Vi": "处女座",
        "Li": "天秤座",
        "Sc": "天蝎座",
        "Sg": "射手座",
        "Cp": "摩羯座",
        "Aq": "水瓶座",
        "Pi": "双鱼座",
    },
    "NAK_LABELS": {
        "Ashwini": "娄宿",
        "Bharani": "胃宿",
        "Krittika": "昴宿",
        "Rohini": "毕宿",
        "Mrigashirsha": "觜宿",
        "Mrigashira": "觜宿",
        "Ardra": "参宿",
        "Punarvasu": "井宿",
        "Pushya": "鬼宿",
        "Ashlesha": "柳宿",
        "Magha": "星宿",
        "Purva Phalguni": "张宿",
        "Uttara Phalguni": "翼宿",
        "Hasta": "轸宿",
        "Chitra": "角宿",
        "Swati": "亢宿",
        "Vishakha": "氐宿",
        "Visakha": "氐宿",
        "Anuradha": "房宿",
        "Jyeshtha": "心宿",
        "Mula": "尾宿",
        "Purva Ashadha": "箕宿",
        "Uttara Ashadha": "斗宿",
        "Shravana": "女宿",
        "Dhanishta": "虚宿",
        "Shatabhisha": "危宿",
        "Purva Bhadrapada": "室宿",
        "Uttara Bhadrapada": "壁宿",
        "Revati": "奎宿",
    },
    "TARA_LABELS": {
        "Janma": "命 (根源/磨练)",
        "Sampat": "财 (财富/资源)",
        "Vipat": "难 (障碍/意外)",
        "Kshem": "安 (安稳/康复)",
        "Pratyari": "敌 (阻碍/反面)",
        "Sadhana": "成 (成就/修行)",
        "Naidhana": "危 (极度压抑)",
        "Mitra": "友 (助力/和谐)",
        "ParamaMitra": "极友 (大吉/圆满)",
    },
    "PLANET_STATUS_LABELS": {
        "retrograde": "R 逆行 (回顾/反复)",
        "exalted": "旺 (能量强劲)",
        "debilitated": "落 (能量虚弱)",
    },
}


def house_bilingual_label(house: int) -> str:
    zh = I18N_LABELS["HOUSE_LABELS"].get(house)
    if zh:
        return f"House {house} ({zh})"
    return f"House {house}"


def house_cn_with_h(house: int) -> str:
    zh = I18N_LABELS["HOUSE_LABELS"].get(house)
    if zh:
        return f"{zh} ({house}H)"
    return f"{house}H"


def dasha_rel_bilingual_label(rel: str) -> str:
    return I18N_LABELS["DASHA_REL_LABELS"].get(rel, rel)


def dimension_bilingual_label(dim: str) -> str:
    m = I18N_LABELS["DIMENSION_LABELS"].get(dim, {})
    en = m.get("en", dim)
    zh = m.get("zh", dim)
    return f"{zh} ({en})"


def planet_zh(planet: str) -> str:
    return I18N_LABELS["PLANET_ZH"].get(planet, planet)


def planet_bilingual_label(planet: str) -> str:
    zh = planet_zh(planet)
    if zh == planet:
        return planet
    return f"{zh} ({planet})"


def rasi_bilingual_label(code: str) -> str:
    zh = I18N_LABELS["RASI_LABELS"].get(code)
    if zh:
        return f"{zh} ({code})"
    return code


def nak_bilingual_label(name_or_abbr: str) -> str:
    x = (name_or_abbr or "").strip()
    if not x:
        return x
    full = x
    if x in NAK_ORDER:
        reverse = {v: k for k, v in FULL_TO_ABBR.items()}
        full = reverse.get(x, x)
    zh = I18N_LABELS["NAK_LABELS"].get(full) or I18N_LABELS["NAK_LABELS"].get(x)
    if zh:
        return f"{zh} ({full})"
    return full


def tara_bilingual_label(label: str) -> str:
    zh = I18N_LABELS["TARA_LABELS"].get(label)
    if zh:
        return f"{zh} ({label})"
    return label


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def rasi_to_index(rasi: str) -> int:
    if rasi not in RASI_ORDER:
        raise ValueError(f"Unknown rasi: {rasi}")
    return RASI_ORDER.index(rasi)


def house_from_lagna_and_moon(lagna_rasi: str, moon_rasi: str) -> int:
    li = rasi_to_index(lagna_rasi)
    mi = rasi_to_index(moon_rasi)
    return ((mi - li) % 12) + 1


def nak_to_index(nak: str) -> int:
    x = (nak or "").strip()
    if "(" in x:
        x = x.split("(")[0].strip()
    x_norm = x.lower().replace(" ", "").replace("-", "")

    if x in NAK_ORDER:
        return NAK_ORDER.index(x)

    full_to_abbr_norm = {
        "ashwini": "Aswi",
        "bharani": "Bhar",
        "krittika": "Krit",
        "rohini": "Rohi",
        "mrigashirsha": "Mrig",
        "mrigashira": "Mrig",
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
        return NAK_ORDER.index(full_to_abbr_norm[x_norm])

    raise ValueError(f"Unknown nakshatra: {nak}")


def tara_bala_label_and_score(natal_nak: str, transit_nak: str) -> Tuple[str, int]:
    n = nak_to_index(natal_nak)
    t = nak_to_index(transit_nak)
    count = ((t - n) % 27) + 1
    tara_idx = ((count - 1) % 9) + 1
    label9 = TARA_INDEX_TO_LABEL[tara_idx]
    label7 = TARA_9CYCLE_TO_7LABEL[label9]
    score = TARA_TABLE[label7]
    return label7, score


def tara_bala_label(natal_nak: str, transit_nak: str) -> str:
    n = nak_to_index(natal_nak)
    t = nak_to_index(transit_nak)
    count = ((t - n) % 27) + 1
    tara_idx = ((count - 1) % 9) + 1
    return TARA_INDEX_TO_LABEL[tara_idx]

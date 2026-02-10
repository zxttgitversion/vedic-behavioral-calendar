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
    "VEDHA_OBSTRUCTION_TEMPLATES": {
        "Sun": {
            "strong": "[好运受阻]：太阳光芒被掩盖，原本提升名望与地位的机会因小人或制度干扰而延迟。",
            "weak": "[名望受阻]：太阳能量微弱，建议暂缓重大曝光和权力争夺。",
        },
        "Moon": {
            "strong": "[心态受阻]：月亮心智被拨乱，原本稳定的情绪和直觉变得模糊，容易产生不必要的焦虑。",
            "weak": "[情绪微弱]：月亮蒙尘，心态波动较大，宜加强冥想与自我觉察。",
        },
        "Mars": {
            "strong": "[执行受阻]：火星刀锋变钝，原本果断的行动力遭遇软绵绵的阻力，切忌因心急而强行发力。",
            "weak": "[斗志消退]：火星能量衰弱，竞争力下降，宜避免冲突与高压环境。",
        },
        "Merc": {
            "strong": "[沟通受阻]：水星信号丢包，原本清晰的逻辑和文书往来出现偏差，看似达成的协议可能存在隐形漏洞。",
            "weak": "[表达不畅]：水星被遮挡，信息传递易失真，重要沟通需多次确认。",
        },
        "Jup": {
            "strong": "[好运受阻]：木星贵人失联，最关键的'神来之笔'被遮挡，外部机会看似很多，但实质性的助力难以落地。",
            "weak": "[贵人隐退]：木星能量微弱，人脉资源难以动员，需要多花精力去维系关系。",
        },
        "Ven": {
            "strong": "[情感/财运受阻]：金星蜜糖掺砂，原本愉悦的社交或进账伴随着小插曲，容易在关键时刻发生审美疲劳或预算超标。",
            "weak": "[吸引力下降]：金星失辉，社交运和财运都不理想，宜降低期待值。",
        },
        "Sat": {
            "strong": "[稳定受阻]：土星防线松动，原本以为万无一失的长期计划因外部环境的突然变动而需要临时打补丁。",
            "weak": "[基础shake]：土星被压制，长期计划需要重新评估，保守策略反而更安全。",
        },
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
    reverse = {v: k for k, v in FULL_TO_ABBR.items()}
    full = x
    if x in NAK_ORDER:
        full = reverse.get(x, x)
    zh = I18N_LABELS["NAK_LABELS"].get(full) or I18N_LABELS["NAK_LABELS"].get(x)

    # Fallback: normalize transliteration variants through nak index resolution.
    if not zh:
        try:
            abbr = NAK_ORDER[nak_to_index(x)]
            full = reverse.get(abbr, abbr)
            zh = (
                I18N_LABELS["NAK_LABELS"].get(full)
                or I18N_LABELS["NAK_LABELS"].get(abbr)
                or I18N_LABELS["NAK_LABELS"].get(x)
            )
        except ValueError:
            pass

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
        "aswini": "Aswi",
        "asvini": "Aswi",
        "ashvini": "Aswi",
        "bharani": "Bhar",
        "krittika": "Krit",
        "rohini": "Rohi",
        "mrigashirsha": "Mrig",
        "mrigasirsha": "Mrig",
        "mrigashira": "Mrig",
        "mrigasira": "Mrig",
        "ardra": "Ardr",
        "punarvasu": "Puna",
        "pushya": "Push",
        "ashlesha": "Asle",
        "aslesha": "Asle",
        "magha": "Magh",
        "poorvaphalguni": "PPha",
        "purvaphalguni": "PPha",
        "uttaraphalguni": "UPha",
        "hasta": "Hast",
        "chitra": "Chit",
        "swati": "Swat",
        "visakha": "Visa",
        "vishakha": "Visa",
        "anuradha": "Anu",
        "jyeshtha": "Jye",
        "jyestha": "Jye",
        "mula": "Mool",
        "moola": "Mool",
        "poorvaashadha": "PSha",
        "purvaashadha": "PSha",
        "purvashadha": "PSha",
        "uttaraashadha": "USha",
        "uttarashadha": "USha",
        "shravana": "Srav",
        "sravana": "Srav",
        "dhanishta": "Dhan",
        "shravishtha": "Dhan",
        "shatabhisha": "Sata",
        "satabhisha": "Sata",
        "shataraka": "Sata",
        "poorvabhadrapada": "PBha",
        "purvabhadrapada": "PBha",
        "purvabhadra": "PBha",
        "uttarabhadrapada": "UBha",
        "uttarabhadra": "UBha",
        "revati": "Reva",
    }

    # Tolerant lookup for common transliteration shifts (JH and regional spellings).
    candidates = {x_norm}
    for key in list(candidates):
        candidates.add(key.replace("oo", "u"))
        candidates.add(key.replace("sh", "s"))
        candidates.add(key.replace("w", "v"))
        candidates.add(key.replace("v", "w"))

    for key in candidates:
        abbr = full_to_abbr_norm.get(key)
        if abbr:
            return NAK_ORDER.index(abbr)

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

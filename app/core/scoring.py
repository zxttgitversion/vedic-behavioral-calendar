# app/core/scoring.py
from datetime import date
from typing import Dict, Any, List

from app.core.daily_features import get_daily_features_stub
from app.core.astrology_rules import (
    clamp, house_from_lagna_and_moon,
    tara_bala_label_and_score, special_flags, apply_special_day_overrides
)

from app.core.rule_loader import load_yaml_rule


def classify_signal(score: float) -> str:
    if score >= 70:
        return "green"
    if score >= 40:
        return "yellow"
    return "red"

def get_tithi_score(tithi: int) -> int:
    # v1.1: 先保留简单版（后面你会换成 YAML 查表）
    # 这里先给一点点波动：2/3/5/6/10/11/13/16/20/21/25/26/28/29 视为“平稳” +5
    stable = {2,3,5,6,10,11,13,16,20,21,25,26,28,29}
    if tithi in stable:
        return 5
    if tithi in (4,9,14):
        return -10
    return 0

def get_dasha_factor(maha: str, antar: str) -> float:
    # v1.1: 查表法，先用你之前建议的轻量版本
    maha_map = {
        "Sat": 0.90, "Jup": 1.05, "Ven": 1.05, "Merc": 1.00, "Sun": 0.98,
        "Moon": 0.98, "Mars": 0.95, "Rah": 0.95, "Ket": 0.92
    }
    base = maha_map.get(maha, 1.0)

    # antar轻微微调（可先都 1.0）
    antar_map = {
        "Sat": 0.99, "Jup": 1.01, "Ven": 1.01, "Merc": 1.00, "Sun": 1.00,
        "Moon": 0.99, "Mars": 0.99, "Rah": 0.99, "Ket": 0.99
    }
    return base * antar_map.get(antar, 1.0)

def get_container_factor() -> float:
    # v1.1: 先不启用 Ashtakavarga，固定 1.0
    return 1.0

def get_house_factor(moon_house: int, enable_av: bool = False) -> float:
    """
    v1.1: house factor driven by YAML config (deterministic).
    v1.2+: if enable_av True, we can override high/low by Ashtakavarga later.
    """
    if moon_house is None:
        return 1.0

    # v1.1 config
    cfg = load_yaml_rule("house.yaml").get("default", {})

    high_houses = set(cfg.get("high_houses", []))
    low_houses = set(cfg.get("low_houses", []))

    high_factor = float(cfg.get("high_factor", 1.1))
    low_factor = float(cfg.get("low_factor", 0.9))
    neutral_factor = float(cfg.get("neutral_factor", 1.0))

    # v1.2+: if enable_av is True, we will compute high/low houses from AV
    # For now, keep deterministic YAML rules (no AV).
    if moon_house in high_houses:
        return high_factor
    if moon_house in low_houses:
        return low_factor
    return neutral_factor

def action_templates(signal: str, flags: List[str]) -> Dict[str, Any]:
    # v1.1: 先按 signal + flags 输出 deterministic 模板
    if "rikta_tithi" in flags:
        return {
            "action_tags": ["maintenance", "avoid_new_starts"],
            "do": ["Handle cleanup tasks", "Review and consolidate"],
            "avoid": ["Start something new", "Make irreversible commitments"],
        }

    if signal == "green":
        return {"action_tags": ["execution", "decision_window"],
                "do": ["Push key tasks", "Make decisions with confidence"],
                "avoid": ["Over-scattering attention"]}
    if signal == "yellow":
        return {"action_tags": ["maintenance"],
                "do": ["Focus on routine tasks", "Plan carefully"],
                "avoid": ["High-risk commitments"]}
    return {"action_tags": ["low_exposure", "avoid_risk"],
            "do": ["Rest and review", "Do low-risk work"],
            "avoid": ["Major decisions", "High-pressure conflicts"]}

def score_day(parsed_profile: Dict[str, Any], d: date) -> Dict[str, Any]:
    natal_nak = parsed_profile["natal_nakshatra_name"]
    maha = parsed_profile.get("dasha_maha", "Unknown")
    antar = parsed_profile.get("dasha_antar", "Unknown")
    lagna_rasi = parsed_profile.get("lagna_rasi", None)

    # daily features (stub for now)
    feat = get_daily_features_stub(d, natal_nak)
    transit_nak = feat["transit_nakshatra"]
    moon_rasi = feat["moon_rasi"]
    tithi = int(feat["tithi"])

    # v1.1 scores
    tara_label, base_score = tara_bala_label_and_score(natal_nak, transit_nak)
    env_score = get_tithi_score(tithi)

    container_factor = get_container_factor()
    dasha_factor = get_dasha_factor(maha, antar)

    # moon house factor (needs lagna)
    if lagna_rasi is None:
        moon_house = None
        house_factor = 1.0
    else:
        moon_house = house_from_lagna_and_moon(lagna_rasi, moon_rasi)
        house_factor = get_house_factor(moon_house, enable_av=False)

    pre = (50 + base_score + env_score)
    pre *= container_factor
    pre *= dasha_factor
    pre *= house_factor

    flags = special_flags(natal_nak, transit_nak, tithi)
    signal = classify_signal(pre)
    signal, pre2 = apply_special_day_overrides(signal, pre, flags, tara_label)

    final = clamp(pre2, 0, 100)

    actions = action_templates(signal, flags)

    return {
        "date": d.isoformat(),
        "day_score": int(round(final)),
        "signal": signal,
        "special_flags": flags,
        "drivers": {
            "tara_bala": tara_label,
            "tithi": tithi,
            "dasha": f"{maha}/{antar}",
            "moon_rasi": moon_rasi,
            "moon_house": moon_house,
        },
        "components": {
            "natal_nakshatra": natal_nak,
            "transit_nakshatra": transit_nak,
            "tara_label": tara_label,
            "base_score": base_score,
            "tithi": tithi,
            "env_score": env_score,
            "lagna_rasi": lagna_rasi,
            "moon_rasi": moon_rasi,
            "moon_house": moon_house,
            "house_factor": house_factor,
            "container_factor": container_factor,
            "dasha_factor": dasha_factor,
            "pre_clamp_score": float(pre2),
        },
        **actions
    }

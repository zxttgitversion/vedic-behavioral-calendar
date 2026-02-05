# app/core/scoring.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, List, Optional, Tuple

from app.core.daily_features import get_daily_features_stub
from app.core.astrology_rules import (
    clamp,
    house_from_lagna_and_moon,
    tara_bala_label_and_score,
)
from app.core.rule_loader import load_yaml_rule


# -----------------------------
# Defaults (used if rules.yaml missing keys)
# -----------------------------

DEFAULT_RULES: Dict[str, Any] = {
    # Step 1: Base score by MD/AD relationship label
    "dasha_relative_matrix": {
        "1/1": 75,
        "2/12": 40,
        "3/11": 85,
        "4/10": 80,
        "5/9": 95,
        "6/8": 35,
        "7/7": 70,
    },
    # Step 2: Tara Bala modifiers (dimension-wise multipliers)
    # Keys are 7-labels from your code: Janma/Sampat/Vipat/Kshema/Pratyari/Sadhana/Naidhana
    "tara_bala_modifiers": {
        "Janma":    {"emotion": 0.9, "wealth": 1.0, "career": 1.0, "social": 1.0, "vitality": 0.8},
        "Sampat":   {"emotion": 1.1, "wealth": 1.3, "career": 1.2, "social": 1.1, "vitality": 1.0},
        "Vipat":    {"emotion": 0.8, "wealth": 0.9, "career": 0.7, "social": 0.8, "vitality": 0.9},
        "Kshema":   {"emotion": 1.2, "wealth": 1.1, "career": 1.1, "social": 1.0, "vitality": 1.2},
        "Pratyari": {"emotion": 0.7, "wealth": 1.0, "career": 0.8, "social": 0.6, "vitality": 0.9},
        "Sadhana":  {"emotion": 1.1, "wealth": 1.2, "career": 1.3, "social": 1.1, "vitality": 1.0},
        "Naidhana": {"emotion": 0.5, "wealth": 0.8, "career": 0.9, "social": 0.7, "vitality": 0.5},
    },
    # Step 3: Gochara house bonus (dimension-wise additive)
    # We only have Moon house right now; later key_transits can add other planets.
    "gochara_rules": {
        "house_bonus": {3: 0.10, 6: 0.10, 10: 0.15, 11: 0.20},  # Upachaya default
        # BAV placeholder thresholds (not used until you parse BAV + compute transit sign)
        "bav_thresholds": {
            "low":  {"range": [0, 2], "mod": -0.20},
            "mid":  {"range": [3, 4], "mod": 0.00},
            "high": {"range": [5, 8], "mod": 0.20},
        },
    },
    # Which house matters most per dimension (placeholder – can be moved to YAML later)
    "dimension_house_focus": {
        "emotion": [4],
        "wealth": [2, 11],
        "career": [10],
        "social": [3, 7],
        "vitality": [1, 6],
    },
    # Signal thresholds for total_index
    "signal_thresholds": {"green": 70, "yellow": 40},
    "clamp": {"min": 5, "max": 99},
}


DIMENSIONS = ["emotion", "wealth", "career", "social", "vitality"]


def _load_rules() -> Dict[str, Any]:
    """
    Load rules.yaml if present. Fall back to DEFAULT_RULES.
    """
    try:
        cfg = load_yaml_rule("rules.yaml")
        # shallow merge (good enough for now)
        merged = dict(DEFAULT_RULES)
        for k, v in (cfg or {}).items():
            merged[k] = v
        return merged
    except Exception:
        return DEFAULT_RULES


# -----------------------------
# Step 1: Base Score (MD/AD relationship)
# -----------------------------

def get_dasha_relationship(maha: str, antar: str, parsed_profile: Dict[str, Any]) -> str:
    """
    TODO (strict version): compute relationship based on MD/AD planets' house positions in natal chart.
    Current (placeholder): deterministic mapping WITHOUT natal positions.

    Why placeholder:
    - current parser provides only maha/antar names.
    - cannot infer 6/8 etc without planet house placements.

    Replace this function once you parse MD/AD planet houses from zz.txt.
    """
    # Safe fallback:
    if maha == antar:
        return "1/1"
    # Very simple placeholder: treat some known-friction pairs as 6/8 (example)
    # You should overwrite with real computation later.
    friction_pairs = {("Sat", "Moon"), ("Moon", "Sat")}
    if (maha, antar) in friction_pairs:
        return "6/8"
    return "7/7"


def compute_base_score(parsed_profile: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    maha = parsed_profile.get("dasha_maha", "Unknown")
    antar = parsed_profile.get("dasha_antar", "Unknown")

    rel = get_dasha_relationship(maha, antar, parsed_profile)
    base_map = rules.get("dasha_relative_matrix", DEFAULT_RULES["dasha_relative_matrix"])
    base = int(base_map.get(rel, 70))  # default to neutral-ish

    return {
        "maha": maha,
        "antar": antar,
        "dasha_relationship": rel,
        "base_score": base,
    }


# -----------------------------
# Step 2: Tara Bala modifiers (dimension-wise)
# -----------------------------

def apply_tara_bala(parsed_profile: Dict[str, Any], feat: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    natal_nak = parsed_profile["natal_nakshatra_name"]
    transit_nak = feat["transit_nakshatra"]

    tara_label, _old_tara_score = tara_bala_label_and_score(natal_nak, transit_nak)
    tara_mods_all = rules.get("tara_bala_modifiers", DEFAULT_RULES["tara_bala_modifiers"])
    mods = tara_mods_all.get(tara_label, {d: 1.0 for d in DIMENSIONS})

    return {
        "natal_nak": natal_nak,
        "transit_nak": transit_nak,
        "tara_label": tara_label,
        "tara_modifiers": {d: float(mods.get(d, 1.0)) for d in DIMENSIONS},
    }


# -----------------------------
# Step 3: Gochara & BAV modifiers (placeholder with Moon house only)
# -----------------------------

def compute_house_and_modifiers(parsed_profile: Dict[str, Any], feat: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    lagna_rasi = parsed_profile.get("lagna_rasi", None)
    moon_rasi = feat["moon_rasi"]

    if lagna_rasi is None:
        moon_house = None
    else:
        moon_house = house_from_lagna_and_moon(lagna_rasi, moon_rasi)

    gochara = rules.get("gochara_rules", DEFAULT_RULES["gochara_rules"])
    house_bonus_table = gochara.get("house_bonus", DEFAULT_RULES["gochara_rules"]["house_bonus"])

    # Generic bonus (same for all dimensions as a baseline)
    generic_house_bonus = float(house_bonus_table.get(moon_house, 0.0)) if moon_house else 0.0

    # Dimension-specific focus (optional extra weight if Moon lands in "important" house for that dimension)
    focus = rules.get("dimension_house_focus", DEFAULT_RULES["dimension_house_focus"])
    dim_house_bonus: Dict[str, float] = {}
    for dim in DIMENSIONS:
        focus_houses = set(focus.get(dim, []))
        dim_house_bonus[dim] = generic_house_bonus if (moon_house in focus_houses) else 0.0

    # BAV not implemented yet (until you parse BAV + compute planet sign)
    bav_bonus = {d: 0.0 for d in DIMENSIONS}

    return {
        "lagna_rasi": lagna_rasi,
        "moon_rasi": moon_rasi,
        "moon_house": moon_house,
        "house_modifiers": dim_house_bonus,  # additive inside (1 + house + bav)
        "bav_modifiers": bav_bonus,
    }


# -----------------------------
# Step 4: Synthesis & Clamping
# -----------------------------

def synthesize_scores(base_score: int,
                      tara_mods: Dict[str, float],
                      house_mods: Dict[str, float],
                      bav_mods: Dict[str, float],
                      rules: Dict[str, Any]) -> Dict[str, Any]:
    clamp_cfg = rules.get("clamp", DEFAULT_RULES["clamp"])
    lo = float(clamp_cfg.get("min", 5))
    hi = float(clamp_cfg.get("max", 99))

    dim_scores: Dict[str, int] = {}
    for dim in DIMENSIONS:
        m_tara = float(tara_mods.get(dim, 1.0))
        m_house = float(house_mods.get(dim, 0.0))
        m_bav = float(bav_mods.get(dim, 0.0))
        raw = base_score * m_tara * (1.0 + m_house + m_bav)
        dim_scores[dim] = int(round(clamp(raw, lo, hi)))

    mx = max(dim_scores.values())
    mean = sum(dim_scores.values()) / len(dim_scores)
    total = int(round(clamp(mx * 0.3 + mean * 0.7, lo, hi)))

    return {"dimensions": dim_scores, "total_index": total}


def classify_signal(total_index: float, rules: Dict[str, Any]) -> str:
    th = rules.get("signal_thresholds", DEFAULT_RULES["signal_thresholds"])
    if total_index >= float(th.get("green", 70)):
        return "green"
    if total_index >= float(th.get("yellow", 40)):
        return "yellow"
    return "red"


def action_templates(signal: str) -> Dict[str, Any]:
    # keep deterministic templates
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


# -----------------------------
# Public API (used by calendar.py)
# -----------------------------

def score_day(parsed_profile: Dict[str, Any], d: date) -> Dict[str, Any]:
    """
    New v1.1 standardized engine output (still keeps legacy keys for UI).
    """
    rules = _load_rules()

    # Dynamic daily features (still stub; Swiss Ephemeris later)
    feat = get_daily_features_stub(d, parsed_profile["natal_nakshatra_name"])

    # Step 1
    base_pack = compute_base_score(parsed_profile, rules)

    # Step 2
    tara_pack = apply_tara_bala(parsed_profile, feat, rules)

    # Step 3
    gochara_pack = compute_house_and_modifiers(parsed_profile, feat, rules)

    # Step 4
    scores_pack = synthesize_scores(
        base_score=base_pack["base_score"],
        tara_mods=tara_pack["tara_modifiers"],
        house_mods=gochara_pack["house_modifiers"],
        bav_mods=gochara_pack["bav_modifiers"],
        rules=rules,
    )

    total_index = scores_pack["total_index"]
    signal = classify_signal(total_index, rules)
    actions = action_templates(signal)

    # Keep UI-compatible keys + add standardized payload
    return {
        "date": d.isoformat(),

        # legacy UI fields (so you don't break templates immediately)
        "day_score": int(total_index),
        "signal": signal,
        "special_flags": [],

        # your new standardized payload
        "user_profile": {
            "lagna": gochara_pack["lagna_rasi"],
            "dasha_period": f"{base_pack['maha']}-{base_pack['antar']}",
            "dasha_relationship": base_pack["dasha_relationship"],
        },
        "scores": {
            "total_index": int(total_index),
            "dimensions": scores_pack["dimensions"],
        },
        "astrological_triggers": {
            "tara_bala": {
                "name": tara_pack["tara_label"],
                "nature": tara_pack["tara_label"],  # placeholder; can map to CN/EN descriptions in YAML
                "impact": "Dimension-wise modifiers applied",  # placeholder
            },
            "key_transits": [
                {
                    "planet": "Moon",
                    "house": gochara_pack["moon_house"],
                    "status": "House bonus applied" if gochara_pack["moon_house"] else "Lagna missing",
                    "note": "Using stub daily features; replace with Swiss Ephemeris",
                }
            ],
        },

        # Keep drivers/components for your current debug UI
        "drivers": {
            "tara_bala": tara_pack["tara_label"],
            "dasha": f"{base_pack['maha']}/{base_pack['antar']}",
            "moon_rasi": gochara_pack["moon_rasi"],
            "moon_house": gochara_pack["moon_house"],
        },
        "components": {
            "natal_nakshatra": tara_pack["natal_nak"],
            "transit_nakshatra": tara_pack["transit_nak"],
            "tara_label": tara_pack["tara_label"],
            "base_score": base_pack["base_score"],
            "lagna_rasi": gochara_pack["lagna_rasi"],
            "moon_rasi": gochara_pack["moon_rasi"],
            "moon_house": gochara_pack["moon_house"],
            "tara_modifiers": tara_pack["tara_modifiers"],
            "house_modifiers": gochara_pack["house_modifiers"],
            "bav_modifiers": gochara_pack["bav_modifiers"],
        },

        **actions,
    }

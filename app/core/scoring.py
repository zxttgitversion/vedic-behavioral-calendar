from __future__ import annotations

from datetime import date
from typing import Dict, Any, List, Optional, Tuple

from app.core.daily_features import get_daily_features_swe
from app.core.astrology_rules import (
    I18N_LABELS,
    clamp,
    dasha_rel_bilingual_label,
    dimension_bilingual_label,
    house_cn_with_h,
    house_from_lagna_and_moon,
    nak_bilingual_label,
    planet_bilingual_label,
    planet_zh,
    rasi_bilingual_label,
    tara_bala_label,
    tara_bilingual_label,
)
from app.core.rule_loader import load_yaml_rule


DEFAULT_RULES: Dict[str, Any] = {
    "dasha_relative_matrix": {
        "5/9": 95,
        "3/11": 90,
        "4/10": 85,
        "1/1": 80,
        "7/7": 75,
        "2/12": 65,
        "6/8": 60,
    },
    "dual_lagna_weights": {
        "default": {"lagna": 0.5, "chandra": 0.5},
        "career": {"lagna": 0.7, "chandra": 0.3},
        "emotion": {"lagna": 0.3, "chandra": 0.7},
    },
    "dimension_weights": {
        "emotion": {"planets": {"Moon": 0.4, "Merc": 0.2}},
        "wealth": {"planets": {"Jup": 0.4, "Ven": 0.2}},
        "career": {"planets": {"Sun": 0.3, "Sat": 0.3}},
        "social": {"planets": {"Ven": 0.4, "Merc": 0.2}},
        "vitality": {"planets": {"Sun": 0.4, "Mars": 0.2}},
    },
    "tara_bala_modifiers": {
        "Janma": {"emotion": 0.9, "wealth": 1.0, "career": 1.0, "social": 1.0, "vitality": 0.8},
        "Sampat": {"emotion": 1.1, "wealth": 1.3, "career": 1.2, "social": 1.1, "vitality": 1.0},
        "Vipat": {"emotion": 0.8, "wealth": 0.9, "career": 0.7, "social": 0.8, "vitality": 0.9},
        "Kshem": {"emotion": 1.2, "wealth": 1.1, "career": 1.1, "social": 1.0, "vitality": 1.2},
        "Pratyari": {"emotion": 0.7, "wealth": 1.0, "career": 0.8, "social": 0.6, "vitality": 0.9},
        "Sadhana": {"emotion": 1.1, "wealth": 1.2, "career": 1.3, "social": 1.1, "vitality": 1.0},
        "Naidhana": {"emotion": 0.5, "wealth": 0.8, "career": 0.9, "social": 0.7, "vitality": 0.5},
        "Mitra": {"emotion": 1.1, "wealth": 1.0, "career": 1.1, "social": 1.3, "vitality": 1.0},
        "ParamaMitra": {"emotion": 1.2, "wealth": 1.1, "career": 1.2, "social": 1.4, "vitality": 1.1},
    },
    "gochara_rules": {
        "house_scores": {
            1: 0.05,
            2: 0.10,
            3: 0.20,
            4: 0.10,
            5: 0.00,
            6: 0.20,
            7: 0.00,
            8: -0.25,
            9: 0.25,
            10: 0.20,
            11: 0.30,
            12: -0.15,
        },
        "vedha_rules": {
            "3": {"obstructor_house": 12, "planet_scope": "all", "exceptions": [["Sun", "Sat"]]},
            "6": {"obstructor_house": 9, "planet_scope": "all", "exceptions": [["Sun", "Sat"]]},
            "11": {"obstructor_house": 5, "planet_scope": "all", "exceptions": []},
            "2": {"obstructor_house": 12, "planet_scope": "venus_only", "exceptions": []},
            "4": {"obstructor_house": 10, "planet_scope": "venus_only", "exceptions": []},
            "12": {"obstructor_house": 2, "planet_scope": "venus_only", "exceptions": []},
        },
    },
    "status_rules": {
        "exalted": {"Sun": "Ar", "Moon": "Ta", "Mars": "Cp", "Merc": "Vi", "Jup": "Cn", "Ven": "Pi", "Sat": "Li"},
        "own_signs": {
            "Sun": ["Le"],
            "Moon": ["Cn"],
            "Mars": ["Ar", "Sc"],
            "Merc": ["Ge", "Vi"],
            "Jup": ["Sg", "Pi"],
            "Ven": ["Ta", "Li"],
            "Sat": ["Cp", "Aq"],
        },
        "debilitated": {"Sun": "Li", "Moon": "Sc", "Mars": "Cn", "Merc": "Pi", "Jup": "Cp", "Ven": "Vi", "Sat": "Ar"},
        "retrograde_multiplier": {"benefic": 0.8, "malefic": 1.2},
        "benefics": ["Jup", "Ven", "Merc", "Moon"],
        "malefics": ["Sun", "Mars", "Sat"],
    },
    "signal_thresholds": {"green": 75, "yellow": 60, "vipat_pratyari_force_green": 85},
    "clamp": {"min": 5, "max": 99},
    "score_model": {
        "dasha_weight": 0.4,
        "daily_dynamic_weight": 0.6,
        "daily_dynamic_baseline": 70,
        "gochara_amplifier": 2.0,
    },
}

DIMENSIONS = ["emotion", "wealth", "career", "social", "vitality"]
PLANET_ALIASES = {
    "Sun": "Sun",
    "Moon": "Moon",
    "Mars": "Mars",
    "Merc": "Merc",
    "Mercury": "Merc",
    "Jup": "Jup",
    "Jupiter": "Jup",
    "Ven": "Ven",
    "Venus": "Ven",
    "Sat": "Sat",
    "Saturn": "Sat",
}


def _load_rules() -> Dict[str, Any]:
    try:
        cfg = load_yaml_rule("rules.yaml")
        merged = dict(DEFAULT_RULES)
        for k, v in (cfg or {}).items():
            merged[k] = v
        return merged
    except Exception:
        return DEFAULT_RULES


def _normalize_planet_name(name: str) -> Optional[str]:
    return PLANET_ALIASES.get((name or "").strip())


def relationship_from_houses(maha_house: int, antar_house: int) -> str:
    diff = (antar_house - maha_house) % 12
    mapping = {
        0: "1/1",
        1: "2/12",
        2: "3/11",
        3: "4/10",
        4: "5/9",
        5: "6/8",
        6: "7/7",
        7: "6/8",
        8: "5/9",
        9: "4/10",
        10: "3/11",
        11: "2/12",
    }
    return mapping[diff]


def get_dasha_relationship(maha: str, antar: str, parsed_profile: Dict[str, Any]) -> str:
    maha_house = parsed_profile.get("dasha_maha_house")
    antar_house = parsed_profile.get("dasha_antar_house")
    if isinstance(maha_house, int) and isinstance(antar_house, int):
        return relationship_from_houses(maha_house, antar_house)
    if maha == antar:
        return "1/1"
    return "7/7"


def compute_base_score(parsed_profile: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    maha = parsed_profile.get("dasha_maha", "Unknown")
    antar = parsed_profile.get("dasha_antar", "Unknown")
    rel = get_dasha_relationship(maha, antar, parsed_profile)
    base_map = rules.get("dasha_relative_matrix", DEFAULT_RULES["dasha_relative_matrix"])
    base = int(base_map.get(rel, 70))
    return {
        "maha": maha,
        "antar": antar,
        "dasha_relationship": rel,
        "base_score": base,
        "maha_house": parsed_profile.get("dasha_maha_house"),
        "antar_house": parsed_profile.get("dasha_antar_house"),
    }


def apply_tara_bala(parsed_profile: Dict[str, Any], feat: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    natal_nak = parsed_profile["natal_nakshatra_name"]
    transit_nak = feat["transit_nakshatra"]
    tara_label9 = tara_bala_label(natal_nak, transit_nak)
    mods_all = rules.get("tara_bala_modifiers", DEFAULT_RULES["tara_bala_modifiers"])
    mods = mods_all.get(tara_label9, {d: 1.0 for d in DIMENSIONS})
    return {
        "natal_nak": natal_nak,
        "transit_nak": transit_nak,
        "tara_label": tara_label9,
        "tara_modifiers": {d: float(mods.get(d, 1.0)) for d in DIMENSIONS},
    }


def _dual_weights_for_dim(dim: str, rules: Dict[str, Any]) -> Tuple[float, float]:
    cfg = rules.get("dual_lagna_weights", DEFAULT_RULES["dual_lagna_weights"])
    dflt = cfg.get("default", {"lagna": 0.5, "chandra": 0.5})
    custom = cfg.get(dim, {})
    wl = float(custom.get("lagna", dflt.get("lagna", 0.5)))
    wc = float(custom.get("chandra", dflt.get("chandra", 0.5)))
    return wl, wc


def _house_score(house: Optional[int], house_scores: Dict[Any, Any]) -> float:
    if house is None:
        return 0.0
    if house in house_scores:
        return float(house_scores[house])
    k = str(house)
    if k in house_scores:
        return float(house_scores[k])
    return 0.0


def _is_exception_pair(target: str, obstructor: str, exceptions: List[List[str]]) -> bool:
    t = _normalize_planet_name(target)
    o = _normalize_planet_name(obstructor)
    if t is None or o is None:
        return False
    for pair in exceptions:
        if len(pair) != 2:
            continue
        a = _normalize_planet_name(pair[0])
        b = _normalize_planet_name(pair[1])
        if a is None or b is None:
            continue
        if {t, o} == {a, b}:
            return True
    return False


def _vedha_hit(target_planet: str,
               target_house: Optional[int],
               base_rasi: Optional[str],
               transit_planets: Dict[str, str],
               vedha_rules: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    if target_house is None or base_rasi is None:
        return False, None

    rule = vedha_rules.get(str(target_house))
    if not isinstance(rule, dict):
        return False, None

    scope = rule.get("planet_scope", "all")
    if scope == "venus_only" and _normalize_planet_name(target_planet) != "Ven":
        return False, None

    obstructor_house = int(rule.get("obstructor_house", -1))
    exceptions = rule.get("exceptions", [])

    for obs, obs_rasi in transit_planets.items():
        obs_n = _normalize_planet_name(obs)
        if obs_n is None:
            continue
        # Filter out Moon (not obstructor)
        if obs_n == "Moon":
            continue
        # Filter out Rahu/Ketu (shadow planets, cannot cast vedha)
        if obs_n in ["Rah", "Ket"]:
            continue
        if obs_n == _normalize_planet_name(target_planet):
            continue
        try:
            h = house_from_lagna_and_moon(base_rasi, obs_rasi)
        except Exception:
            continue
        if h != obstructor_house:
            continue
        if _is_exception_pair(target_planet, obs_n, exceptions):
            continue
        return True, {
            "obstructor": obs_n,
            "obstructor_house": obstructor_house,
            "target_house": target_house,
        }

    return False, None


def _status_multiplier(planet: str,
                       transit_rasi: str,
                       is_retrograde: bool,
                       rules: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    cfg = rules.get("status_rules", DEFAULT_RULES["status_rules"])
    p = _normalize_planet_name(planet) or planet

    exalted = cfg.get("exalted", {})
    own_signs = cfg.get("own_signs", {})
    debilitated = cfg.get("debilitated", {})
    retro = cfg.get("retrograde_multiplier", {"benefic": 0.8, "malefic": 1.2})
    benefics = set(cfg.get("benefics", []))
    malefics = set(cfg.get("malefics", []))

    is_exalted = exalted.get(p) == transit_rasi
    is_own = transit_rasi in own_signs.get(p, [])
    is_debilitated = debilitated.get(p) == transit_rasi

    m = 1.0
    if is_debilitated:
        m = 0.60
    elif is_exalted:
        m = 1.25
    elif is_own:
        m = 1.10

    if is_retrograde:
        if p in benefics:
            m *= float(retro.get("benefic", 0.8))
        elif p in malefics:
            m *= float(retro.get("malefic", 1.2))

    return m, {
        "is_exalted": bool(is_exalted),
        "is_own_sign": bool(is_own),
        "is_debilitated": bool(is_debilitated),
        "is_retrograde": bool(is_retrograde),
        "status_multiplier": float(m),
    }


def _planet_status_label(status_pack: Dict[str, Any]) -> str:
    labels: List[str] = []
    status_labels = I18N_LABELS.get("PLANET_STATUS_LABELS", {})
    if status_pack.get("is_debilitated"):
        labels.append(status_labels.get("debilitated", "落"))
    elif status_pack.get("is_exalted"):
        labels.append(status_labels.get("exalted", "旺"))
    if status_pack.get("is_retrograde"):
        labels.append(status_labels.get("retrograde", "R 逆行"))
    if not labels:
        return "平稳"
    return " / ".join(labels)


def compute_gochara_v2(parsed_profile: Dict[str, Any], feat: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    lagna_rasi = parsed_profile.get("lagna_rasi")
    natal_moon_rasi = parsed_profile.get("natal_moon_rasi")
    if natal_moon_rasi is None:
        natal_moon_rasi = (parsed_profile.get("planet_rasi") or {}).get("Moon")

    transit_planets = feat.get("planet_rasi", {}) or {}
    transit_motion = feat.get("planet_status", {}) or {}
    moon_rasi = transit_planets.get("Moon", feat.get("moon_rasi"))
    moon_house = house_from_lagna_and_moon(lagna_rasi, moon_rasi) if lagna_rasi and moon_rasi else None

    gochara = rules.get("gochara_rules", DEFAULT_RULES["gochara_rules"])
    house_scores = gochara.get("house_scores", DEFAULT_RULES["gochara_rules"]["house_scores"])
    vedha_rules = gochara.get("vedha_rules", DEFAULT_RULES["gochara_rules"]["vedha_rules"])
    dim_cfg = rules.get("dimension_weights", DEFAULT_RULES["dimension_weights"])

    dim_gochara_mod: Dict[str, float] = {}
    dim_lagna_view: Dict[str, float] = {}
    dim_chandra_view: Dict[str, float] = {}
    key_transits: List[Dict[str, Any]] = []

    transit_status: Dict[str, Dict[str, Any]] = {}
    vedha_impact: Dict[str, Dict[str, Any]] = {}
    chandra_gochara: Dict[str, Dict[str, Any]] = {}

    obstruction_records: List[Tuple[str, str]] = []

    for dim in DIMENSIONS:
        cfg = dim_cfg.get(dim, {})
        planets = cfg.get("planets", {})
        w_l, w_c = _dual_weights_for_dim(dim, rules)

        dim_total = 0.0
        lagna_view = 0.0
        chandra_view = 0.0

        dominant = None
        dominant_w = -1.0

        for p_name, p_weight in planets.items():
            p = _normalize_planet_name(p_name)
            if p is None:
                continue
            w = float(p_weight)
            transit_rasi = transit_planets.get(p)
            if transit_rasi is None:
                continue

            h_l = house_from_lagna_and_moon(lagna_rasi, transit_rasi) if lagna_rasi else None
            h_c = house_from_lagna_and_moon(natal_moon_rasi, transit_rasi) if natal_moon_rasi else None
            s_l = _house_score(h_l, house_scores)
            s_c = _house_score(h_c, house_scores)
            s_raw = (s_l * w_l) + (s_c * w_c)

            vedha_hit = False
            vedha_by = None
            vedha_basis = []

            hit_l, detail_l = _vedha_hit(p, h_l, lagna_rasi, transit_planets, vedha_rules)
            if hit_l:
                vedha_hit = True
                vedha_by = detail_l["obstructor"]
                vedha_basis.append("lagna")

            hit_c, detail_c = _vedha_hit(p, h_c, natal_moon_rasi, transit_planets, vedha_rules)
            if hit_c:
                vedha_hit = True
                vedha_by = vedha_by or detail_c["obstructor"]
                vedha_basis.append("chandra")

            if vedha_hit and s_raw > 0:
                s_raw = 0.0
                if vedha_by:
                    # Track obstruction strength: strong if Chandra-detected, weak if only Lagna
                    is_strong_obstruction = "chandra" in vedha_basis
                    obstruction_records.append((p, vedha_by, is_strong_obstruction, vedha_basis))

            is_retro = bool((transit_motion.get(p) or {}).get("is_retrograde", False))
            m_status, status_pack = _status_multiplier(p, transit_rasi, is_retro, rules)
            s_final = s_raw * m_status

            dim_total += w * s_final
            lagna_view += w * s_l
            chandra_view += w * s_c

            transit_status[p] = status_pack
            vedha_impact[p] = {
                "is_obstructed": bool(vedha_hit),
                "obstructor": vedha_by,
                "obstructor_zh": planet_zh(vedha_by) if vedha_by else None,
                "basis": vedha_basis,
            }
            chandra_gochara[p] = {
                "transit_rasi": transit_rasi,
                "house_from_natal_moon": h_c,
                "score": s_c,
            }

            if w > dominant_w:
                dominant_w = w
                status_label = _planet_status_label(status_pack)
                dominant = {
                    "dimension": dim,
                    "dimension_label": dimension_bilingual_label(dim),
                    "planet": p,
                    "planet_zh": planet_zh(p),
                    "planet_display": planet_bilingual_label(p),
                    "house_lagna": h_l,
                    "house_chandra": h_c,
                    "lagna_house_label": house_cn_with_h(h_l) if isinstance(h_l, int) else "N/A",
                    "chandra_house_label": house_cn_with_h(h_c) if isinstance(h_c, int) else "N/A",
                    "lagna_score": s_l,
                    "chandra_score": s_c,
                    "s_raw": s_raw,
                    "status_multiplier": m_status,
                    "s_final": s_final,
                    "vedha": vedha_impact[p],
                    "status": status_pack,
                    "status_label": status_label,
                    "note": f"{dim}: {planet_bilingual_label(p)} | Lagna {house_cn_with_h(h_l) if isinstance(h_l, int) else 'N/A'} | Chandra {house_cn_with_h(h_c) if isinstance(h_c, int) else 'N/A'} | {status_label}",
                }

        dim_gochara_mod[dim] = float(dim_total)
        dim_lagna_view[dim] = float(lagna_view)
        dim_chandra_view[dim] = float(chandra_view)
        if dominant is not None:
            key_transits.append(dominant)

    obstruction_msg = None
    strong_obstruction_found = False
    
    # Only show top-level warning (yellow frame) if Chandra-detected (strong) obstruction exists
    for record in obstruction_records:
        if len(record) == 4:
            p, obs, is_strong, basis = record
        else:
            # Fallback for old 2-tuple format
            p, obs = record
            is_strong = False
            basis = []
        
        if is_strong and not strong_obstruction_found:
            # Show this as the main obstruction message (top yellow frame)
            obstruction_msg = _get_obstruction_message(p, obs, True)
            strong_obstruction_found = True
            break
    
    # If no strong obstruction, check for weak ones (but don't show top-level warning)
    if not strong_obstruction_found and obstruction_records:
        # Weak obstruction exists but won't be shown as top-level alert
        # It will still be visible in vedha_impact for transparency
        pass

    return {
        "lagna_rasi": lagna_rasi,
        "natal_moon_rasi": natal_moon_rasi,
        "moon_rasi": moon_rasi,
        "moon_house": moon_house,
        "gochara_modifiers": dim_gochara_mod,
        "lagna_view": dim_lagna_view,
        "chandra_view": dim_chandra_view,
        "key_transits": key_transits,
        "transit_status": transit_status,
        "vedha_impact": vedha_impact,
        "chandra_gochara": chandra_gochara,
        "obstruction_message": obstruction_msg,
    }


def _get_obstruction_message(target_planet: str, obstructor: str, is_strong: bool) -> str:
    """
    Generate differentiated obstruction message based on target planet and obstruction strength.
    
    Args:
        target_planet: Normalized planet name (e.g., "Sun", "Moon", "Jup")
        obstructor: Normalized obstructor planet name
        is_strong: True if Chandra-detected (strong), False if only Lagna-detected (weak)
        
    Returns:
        Localized obstruction message
    """
    templates = I18N_LABELS.get("VEDHA_OBSTRUCTION_TEMPLATES", {})
    planet_templates = templates.get(target_planet, {})
    
    strength = "strong" if is_strong else "weak"
    msg = planet_templates.get(strength)
    
    if msg:
        return msg
    
    # Fallback generic message
    if is_strong:
        return f"[好运受阻]：{planet_zh(target_planet)} 被 {planet_zh(obstructor)} 遮蔽，需要谨慎推进计划。"
    else:
        return f"[轻度阻碍]：{planet_zh(target_planet)} 能量有所减弱，宜保持低调。"


def synthesize_scores(base_score: int,
                      tara_mods: Dict[str, float],
                      gochara_mods: Dict[str, float],
                      rules: Dict[str, Any]) -> Dict[str, Any]:
    clamp_cfg = rules.get("clamp", DEFAULT_RULES["clamp"])
    lo = float(clamp_cfg.get("min", 5))
    hi = float(clamp_cfg.get("max", 99))
    model_cfg = rules.get("score_model", DEFAULT_RULES["score_model"])
    dasha_w = float(model_cfg.get("dasha_weight", 0.4))
    daily_w = float(model_cfg.get("daily_dynamic_weight", 0.6))
    daily_base = float(model_cfg.get("daily_dynamic_baseline", 70))
    gochara_amp = float(model_cfg.get("gochara_amplifier", 2.0))
    w_sum = dasha_w + daily_w
    if w_sum <= 0:
        dasha_w, daily_w = 0.4, 0.6
    elif abs(w_sum - 1.0) > 1e-9:
        dasha_w, daily_w = dasha_w / w_sum, daily_w / w_sum

    dim_scores: Dict[str, int] = {}
    dim_breakdown: Dict[str, Dict[str, float]] = {}
    for dim in DIMENSIONS:
        m_tara = float(tara_mods.get(dim, 1.0))
        m_gochara = float(gochara_mods.get(dim, 0.0))
        dasha_component = float(base_score)
        m_gochara_amplified = m_gochara * gochara_amp
        daily_dynamic_component = daily_base * m_tara * (1.0 + m_gochara_amplified)
        raw = (dasha_component * dasha_w) + (daily_dynamic_component * daily_w)
        dim_scores[dim] = int(round(clamp(raw, lo, hi)))
        dim_breakdown[dim] = {
            "dasha_component": dasha_component,
            "daily_dynamic_component": daily_dynamic_component,
            "tara_modifier": m_tara,
            "gochara_modifier": m_gochara,
            "gochara_modifier_amplified": m_gochara_amplified,
            "raw_before_clamp": raw,
        }

    mx = max(dim_scores.values())
    mean = sum(dim_scores.values()) / len(dim_scores)
    total = int(round(clamp(mx * 0.3 + mean * 0.7, lo, hi)))
    return {
        "dimensions": dim_scores,
        "total_index": total,
        "dimension_breakdown": dim_breakdown,
        "score_model": {
            "dasha_weight": dasha_w,
            "daily_dynamic_weight": daily_w,
            "daily_dynamic_baseline": daily_base,
            "gochara_amplifier": gochara_amp,
        },
    }


def classify_signal(total_index: float, tara_label: str, rules: Dict[str, Any]) -> str:
    if tara_label == "Naidhana":
        return "red"

    th = rules.get("signal_thresholds", DEFAULT_RULES["signal_thresholds"])
    if total_index >= float(th.get("green", 70)):
        if tara_label in {"Vipat", "Pratyari"} and total_index < float(th.get("vipat_pratyari_force_green", 85)):
            return "yellow"
        return "green"
    if total_index >= float(th.get("yellow", 60)):
        return "yellow"
    return "red"


def action_templates(signal: str) -> Dict[str, Any]:
    if signal == "green":
        return {
            "action_tags": ["execution", "decision_window"],
            "do": ["Push key tasks", "Make decisions with confidence"],
            "avoid": ["Over-scattering attention"],
        }
    if signal == "yellow":
        return {
            "action_tags": ["maintenance"],
            "do": ["Focus on routine tasks", "Plan carefully"],
            "avoid": ["High-risk commitments"],
        }
    return {
        "action_tags": ["low_exposure", "avoid_risk"],
        "do": ["Rest and review", "Do low-risk work"],
        "avoid": ["Major decisions", "High-pressure conflicts"],
    }


def score_day(parsed_profile: Dict[str, Any], d: date) -> Dict[str, Any]:
    rules = _load_rules()
    feat = get_daily_features_swe(d, parsed_profile["natal_nakshatra_name"])

    base_pack = compute_base_score(parsed_profile, rules)
    tara_pack = apply_tara_bala(parsed_profile, feat, rules)
    gochara_pack = compute_gochara_v2(parsed_profile, feat, rules)

    scores_pack = synthesize_scores(
        base_score=base_pack["base_score"],
        tara_mods=tara_pack["tara_modifiers"],
        gochara_mods=gochara_pack["gochara_modifiers"],
        rules=rules,
    )

    total_index = scores_pack["total_index"]
    signal = classify_signal(total_index, tara_pack["tara_label"], rules)
    actions = action_templates(signal)
    rel_code = base_pack["dasha_relationship"]

    return {
        "date": d.isoformat(),
        "day_score": int(total_index),
        "signal": signal,
        "special_flags": [],
        "user_profile": {
            "lagna": gochara_pack["lagna_rasi"],
            "lagna_display": rasi_bilingual_label(gochara_pack["lagna_rasi"]) if gochara_pack["lagna_rasi"] else None,
            "natal_moon_rasi": gochara_pack["natal_moon_rasi"],
            "natal_moon_rasi_display": (
                rasi_bilingual_label(gochara_pack["natal_moon_rasi"]) if gochara_pack["natal_moon_rasi"] else None
            ),
            "dasha_period": f"{base_pack['maha']}-{base_pack['antar']}",
            "dasha_relationship_code": rel_code,
            "dasha_relationship": dasha_rel_bilingual_label(rel_code),
        },
        "scores": {
            "total_index": int(total_index),
            "dimensions": scores_pack["dimensions"],
            "dimension_breakdown": scores_pack.get("dimension_breakdown", {}),
            "score_model": scores_pack.get("score_model", {}),
        },
        "astrological_triggers": {
            "tara_bala": {
                "name": tara_bilingual_label(tara_pack["tara_label"]),
                "nature": tara_bilingual_label(tara_pack["tara_label"]),
                "impact": "Dimension-wise modifiers applied",
            },
            "obstruction": {
                "has_obstruction": bool(gochara_pack["obstruction_message"]),
                "message": gochara_pack["obstruction_message"],
            },
            "key_transits": gochara_pack["key_transits"],
        },
        "drivers": {
            "tara_bala": tara_pack["tara_label"],
            "dasha": f"{base_pack['maha']}/{base_pack['antar']}",
            "moon_rasi": gochara_pack["moon_rasi"],
            "moon_house": gochara_pack["moon_house"],
        },
        "components": {
            "natal_nakshatra": tara_pack["natal_nak"],
            "natal_nakshatra_display": nak_bilingual_label(tara_pack["natal_nak"]),
            "transit_nakshatra": tara_pack["transit_nak"],
            "transit_nakshatra_display": nak_bilingual_label(tara_pack["transit_nak"]),
            "tara_label": tara_pack["tara_label"],
            "tara_label_display": tara_bilingual_label(tara_pack["tara_label"]),
            "base_score": base_pack["base_score"],
            "lagna_rasi": gochara_pack["lagna_rasi"],
            "natal_moon_rasi": gochara_pack["natal_moon_rasi"],
            "moon_rasi": gochara_pack["moon_rasi"],
            "moon_house": gochara_pack["moon_house"],
            "tara_modifiers": tara_pack["tara_modifiers"],
            "gochara_modifiers": gochara_pack["gochara_modifiers"],
            "dimension_labels": I18N_LABELS.get("DIMENSION_LABELS", {}),
            "house_labels": I18N_LABELS.get("HOUSE_LABELS", {}),
            "dasha_rel_labels": I18N_LABELS.get("DASHA_REL_LABELS", {}),
            "module_titles": I18N_LABELS.get("MODULE_TITLES", {}),
            "field_labels": I18N_LABELS.get("FIELD_LABELS", {}),
            "dual_view": {
                "lagna_view": gochara_pack["lagna_view"],
                "chandra_view": gochara_pack["chandra_view"],
            },
            "transit_status": gochara_pack["transit_status"],
            "vedha_impact": gochara_pack["vedha_impact"],
            "chandra_gochara": gochara_pack["chandra_gochara"],
            "transit_planet_rasi": feat.get("planet_rasi", {}),
        },
        "summary_llm": "[Bilingual Placeholder] 今日外界环境压力较大，但你内在感知平稳。利于深入思考，不宜强行推进外在事务。",  # TODO: LLM API Integration
        **actions,
    }

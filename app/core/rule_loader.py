from pathlib import Path
from functools import lru_cache
from typing import Any, Dict

import yaml

# app/core/rule_loader.py
# This file loads deterministic rules from YAML under app/rules/.

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"


@lru_cache(maxsize=32)
def load_yaml_rule(filename: str) -> Dict[str, Any]:
    """
    Load YAML rule file from app/rules/*.yaml
    Cached for performance and determinism.
    """
    path = RULES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Rule file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid rule format in {filename}: expected dict at top level")
    return data

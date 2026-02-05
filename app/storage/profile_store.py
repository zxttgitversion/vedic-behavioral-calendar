import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parents[2]  # project root
PROFILES_DIR = BASE_DIR / "storage" / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

def save_profile(file_id: str, data: Dict[str, Any]) -> Path:
    path = PROFILES_DIR / f"{file_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def load_profile(file_id: str) -> Dict[str, Any]:
    path = PROFILES_DIR / f"{file_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"profile not found: {file_id}")
    return json.loads(path.read_text(encoding="utf-8"))

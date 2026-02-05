# app/core/constants.py

PLANETS = {"Sun", "Moon", "Mars", "Merc", "Jup", "Ven", "Sat", "Rah", "Ket"}

RASI_ORDER = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

# 27 Nakshatra order (no Abhijit). Use your preferred spelling.
NAK_ORDER = [
    "Aswi","Bhar","Krit","Rohi","Mrig","Ardr","Puna","Push","Asle",
    "Magh","PPha","UPha","Hast","Chit","Swat","Visa","Anu","Jye",
    "Mool","PSha","USha","Srav","Dhan","Sata","PBha","UBha","Reva"
]

NAK_EN = {
    "Visa": "Visakha",
    "Chit": "Chitra",
    "Anu": "Anuradha",
    # ...你可以慢慢补全；没补全就 fallback 原样
}

NAK_ZH = {
    "Visa": "毗舍佉（分叉宿）",
    "Chit": "吉塔（室女宿/角宿系，按你习惯填）",
    "Anu": "随宿",
}

TARA_TABLE = {
    # label: score
    "Sadhana": 20,
    "Sampat": 15,
    "Kshem": 10,
    "Neutral": 0,
    "Pratyari": -15,
    "Vipat": -20,
    "Naidhana": -25,
}

# Tara index mapping (1..9) -> label. We'll implement standard Tara Bala cycle:
TARA_INDEX_TO_LABEL = {
    1: "Janma",      # 我们会单独作为 special flag，不直接给分
    2: "Sampat",
    3: "Vipat",
    4: "Kshem",
    5: "Pratyari",
    6: "Sadhana",
    7: "Naidhana",
    8: "Mitra",
    9: "ParamaMitra",
}

# In v1.1 we map the 9-cycle to our 7 labels (fold Mitra/ParamaMitra to Sampat/Kshem or Neutral)
TARA_9CYCLE_TO_7LABEL = {
    "Janma": "Neutral",
    "Sampat": "Sampat",
    "Vipat": "Vipat",
    "Kshem": "Kshem",
    "Pratyari": "Pratyari",
    "Sadhana": "Sadhana",
    "Naidhana": "Naidhana",
    "Mitra": "Sampat",
    "ParamaMitra": "Kshem",
}

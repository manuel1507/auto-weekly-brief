# src/enrich/rank.py

from typing import Dict, List


def score_event(event: Dict, keyword_map: Dict[str, List[str]]) -> int:
    """
    Tier-1 / Tier-2 oriented scoring.

    Strong emphasis on vehicle production, capacity,
    plant operations and supply disruptions.

    Returns score in range [0, 100].
    """

    title = (event.get("title") or "")
    text = (event.get("text") or "")
    blob = f"{title} {text}".lower()

    score = 0

    # ---------------------------------------------------------
    # 1) Baseline category scoring (from config KEYWORDS)
    # ---------------------------------------------------------

    weights = {
        "footprint_ops": 18,
        "policy_trade": 16,
        "quality_recalls": 14,
        "electronics_sdv": 12,
        "ev_battery": 12,
        "suppliers": 12,
        "oem_demand": 8,
    }

    for cat, kws in (keyword_map or {}).items():
        hits = 0
        for kw in kws:
            if kw and kw.lower() in blob:
                hits += 1
        if hits:
            score += min(2, hits) * weights.get(cat, 6)

    # ---------------------------------------------------------
    # 2) PRODUCTION IMPACT BOOST (multilingual)
    # ---------------------------------------------------------

    PRODUCTION_KEYWORDS = {
        # ---------------- ENGLISH ----------------
        "start of production": 22,
        "sop": 22,
        "job 1": 18,
        "ramp up": 20,
        "ramp-up": 20,
        "ramp down": 20,
        "ramp-down": 20,
        "capacity": 16,
        "utilization": 14,
        "output": 14,
        "production": 16,
        "production halt": 24,
        "shutdown": 26,
        "temporary shutdown": 24,
        "plant": 12,
        "factory": 12,
        "assembly": 14,
        "assembly line": 18,
        "line stoppage": 22,
        "shift reduction": 24,
        "reduced shifts": 20,
        "third shift": 16,
        "strike": 20,
        "labor strike": 22,
        "closure": 26,
        "plant closure": 28,
        "capacity expansion": 18,
        "battery plant": 18,
        "gigafactory": 16,
        "chip shortage": 18,
        "semiconductor shortage": 18,
        "supply disruption": 18,
        "stop production": 24,
        "stops production": 24,

        # ---------------- ITALIAN ----------------
        "produzione": 16,
        "impianto": 14,
        "stabilimento": 14,
        "linea di produzione": 20,
        "fermo produzione": 26,
        "stop produzione": 26,
        "chiusura": 24,
        "chiusura impianto": 28,
        "riduzione turni": 26,
        "riduce i turni": 24,
        "taglio produzione": 22,
        "capacità produttiva": 18,
        "avvio produzione": 22,
        "sospensione produzione": 24,
        "sciopero": 20,

        # ---------------- GERMAN ----------------
        "produktion": 16,
        "werk": 14,
        "werksschließung": 28,
        "produktion gestoppt": 26,
        "schichtabbau": 26,
        "kapazität": 18,
        "fertigung": 16,
        "stilllegung": 26,
    }

    for kw, weight in PRODUCTION_KEYWORDS.items():
        if kw in blob:
            score += weight

    # ---------------------------------------------------------
    # 3) LOW IMPACT / NOISE DEBOOST
    # ---------------------------------------------------------

    LOW_IMPACT_KEYWORDS = {
        "concept": -10,
        "rendering": -6,
        "teaser": -6,
        "facelift": -6,
        "award": -8,
        "design": -6,
        "limited edition": -6,
        "valuation": -6,
        "funding": -5,
        "raises": -4,
        "seed round": -6,
        "series a": -6,
        "series b": -6,
        "influencer": -10,
    }

    for kw, weight in LOW_IMPACT_KEYWORDS.items():
        if kw in blob:
            score += weight

    # ---------------------------------------------------------
    # 4) Normalize score to 0–100
    # ---------------------------------------------------------

    if score < 0:
        score = 0
    if score > 120:
        score = 120

    score = int(round(score * (100.0 / 120.0)))

    if score > 100:
        score = 100

    return score


def classify_event(event: Dict, keyword_map: Dict[str, List[str]]) -> str:
    """
    Assign one primary category based on keyword hits.
    """

    title = (event.get("title") or "")
    text = (event.get("text") or "")
    blob = f"{title} {text}".lower()

    if not keyword_map:
        return "other"

    counts = {}
    for cat, kws in keyword_map.items():
        counts[cat] = sum(1 for kw in kws if kw and kw.lower() in blob)

    best = max(counts, key=lambda k: counts[k])
    return best if counts[best] > 0 else "other"

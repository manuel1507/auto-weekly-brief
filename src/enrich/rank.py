from collections import Counter
from typing import Dict, List

def score_event(event: Dict, keyword_map: Dict[str, List[str]]) -> int:
    """
    Simple deterministic Tier-1 impact scoring.
    You can tune weights later.
    """
    text = (event.get("title","") + " " + event.get("text","")).lower()
    score = 0

    weights = {
        "footprint_ops": 20,
        "policy_trade": 18,
        "quality_recalls": 18,
        "electronics_sdv": 16,
        "ev_battery": 14,
        "suppliers": 14,
        "oem_demand": 10,
    }

    for cat, kws in keyword_map.items():
        hits = sum(1 for kw in kws if kw.lower() in text)
        if hits:
            score += min(2, hits) * weights.get(cat, 8)

    # Prefer official/regulator sources when you later add them (placeholder hook)
    return min(score, 100)

def classify_event(event: Dict, keyword_map: Dict[str, List[str]]) -> str:
    text = (event.get("title","") + " " + event.get("text","")).lower()
    counts = {}
    for cat, kws in keyword_map.items():
        counts[cat] = sum(1 for kw in kws if kw.lower() in text)
    best = max(counts, key=lambda k: counts[k])
    return best if counts[best] > 0 else "other"
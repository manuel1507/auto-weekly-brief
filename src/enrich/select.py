from __future__ import annotations

from typing import Dict, List
from urllib.parse import urlparse

from src.config import INDUSTRIAL_SIGNALS, DEPRIORITIZE_SIGNALS


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _blob(e: dict) -> str:
    title = (e.get("title") or "")
    seed = (e.get("summary_seed") or "")
    return f"{title} {seed}".lower()


def _has_any(blob: str, terms: List[str]) -> bool:
    return any(t.lower() in blob for t in terms if t)


def _is_supplybase_core(e: dict) -> bool:
    blob = _blob(e)
    # Strong signal: industrial keywords
    if _has_any(blob, INDUSTRIAL_SIGNALS):
        return True
    # Otherwise allow only if already scored high
    try:
        return int(e.get("score") or 0) >= 70
    except Exception:
        return False


def _is_deprioritized(e: dict) -> bool:
    blob = _blob(e)
    # If it contains deprioritize terms AND does not contain strong industrial signals, drop it
    if _has_any(blob, DEPRIORITIZE_SIGNALS) and not _has_any(blob, INDUSTRIAL_SIGNALS):
        return True
    return False


def _bucket(e: dict) -> str:
    """Deterministic bucket assignment."""
    blob = _blob(e)

    # Footprint & Capacity
    if _has_any(blob, [
        "plant", "factory", "facility", "site", "stabilimento", "impianto", "werk",
        "capacity", "utilization", "throughput", "ramp", "shift", "line",
        "shutdown", "closure", "production", "output", "assembly", "capex", "investment", "expansion",
        "new facility", "greenfield", "brownfield"
    ]):
        return "Footprint & Capacity"

    # Ownership / distress / compliance structures
    if _has_any(blob, [
        "acquire", "acquisition", "merger", "m&a", "takeover", "divest", "spin-off", "sale",
        "bankruptcy", "insolvency", "restructuring", "administration", "private equity",
        "emissions", "co2", "pool", "compliance"
    ]):
        return "Ownership, Financial Stress & Compliance"

    # Trade / energy / macro cost base
    if _has_any(blob, [
        "tariff", "duty", "trade", "regulation", "subsidy", "ban",
        "oil", "gas", "energy", "electricity", "inflation", "freight", "shipping", "logistics"
    ]):
        return "Trade, Energy & Cost Base"

    # Tech / manufacturing / industrialisation
    return "Technology & Manufacturing"


def select_and_allocate_events(
    events: List[dict],
    *,
    max_total: int = 18,
    max_per_domain: int = 3,
) -> Dict[str, List[dict]]:
    """
    Select 15–20 supplier-relevant events and allocate them into 4 buckets.
    This prevents the LLM from pulling in consumer noise or repeating the same story in multiple sections.
    """
    # 1) filter
    filtered = []
    for e in events:
        if _is_deprioritized(e):
            continue
        if _is_supplybase_core(e):
            filtered.append(e)

    # 2) sort (keep your current scoring as primary key)
    filtered.sort(key=lambda x: (int(x.get("score") or 0), x.get("published_at") or ""), reverse=True)

    # 3) domain cap + select max_total
    selected: List[dict] = []
    domain_counts: Dict[str, int] = {}
    for e in filtered:
        d = _domain(e.get("url", ""))
        if d and domain_counts.get(d, 0) >= max_per_domain:
            continue
        selected.append(e)
        if d:
            domain_counts[d] = domain_counts.get(d, 0) + 1
        if len(selected) >= max_total:
            break

    # 4) allocate
    buckets = {
        "Footprint & Capacity": [],
        "Ownership, Financial Stress & Compliance": [],
        "Trade, Energy & Cost Base": [],
        "Technology & Manufacturing": [],
    }
    for e in selected:
        buckets[_bucket(e)].append(e)

    return buckets
from __future__ import annotations

from typing import Dict, List
from urllib.parse import urlparse

from src.config import INDUSTRIAL_SIGNALS, DEPRIORITIZE_SIGNALS


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _blob(event: Dict) -> str:
    title = (event.get("title") or "")
    seed = (event.get("summary_seed") or "")
    return f"{title} {seed}".lower()


def _has_any(blob: str, terms: List[str]) -> bool:
    return any(t.lower() in blob for t in terms if t)


def _is_deprioritized(event: Dict) -> bool:
    """
    Drop consumer / PR / low industrial-value items unless there is a strong
    industrial signal in the same event.
    """
    blob = _blob(event)
    has_negative = _has_any(blob, DEPRIORITIZE_SIGNALS)
    has_positive = _has_any(blob, INDUSTRIAL_SIGNALS)
    return has_negative and not has_positive


def _is_supply_base_core(event: Dict) -> bool:
    """
    Keep events that clearly matter for Tier-1 / Tier-2 suppliers.
    """
    blob = _blob(event)

    if _has_any(blob, INDUSTRIAL_SIGNALS):
        return True

    try:
        score = int(event.get("score") or 0)
    except Exception:
        score = 0

    return score >= 70


def select_events(
    events: List[Dict],
    *,
    max_total,
    max_per_domain,
) -> List[Dict]:
    """
    Deterministic selection of the best supplier-relevant events.
    No section allocation here: just filter, rank, diversify, and take top N.
    """
    # 1) filter out weak / noisy items
    filtered: List[Dict] = []
    for event in events:
        if _is_deprioritized(event):
            continue
        if _is_supply_base_core(event):
            filtered.append(event)

    print("\n===== FILTERED EVENTS =====\n")
    for i, z in enumerate(events):
        print(f"{i+1}. {z.get('title','NO TITLE')}")
    print("\n===== END FILTERED =====\n")

    # 2) sort by score, then by publication date
    filtered.sort(
        key=lambda e: (int(e.get("score") or 0), e.get("published_at") or ""),
        reverse=True,
    )

    print("\n===== SORTED EVENTS =====\n")
    for i, z in enumerate(events):
        print(f"{i+1}. {z.get('title','NO TITLE')}")
    print("\n===== END SORTED =====\n")

    # 3) apply domain cap for source diversity
    selected: List[Dict] = []
    domain_counts: Dict[str, int] = {}

    for event in filtered:
        d = _domain(event.get("url", ""))
        if d and domain_counts.get(d, 0) >= max_per_domain:
            continue

        selected.append(event)

        if d:
            domain_counts[d] = domain_counts.get(d, 0) + 1

        if len(selected) >= max_total:
            break

    return selected
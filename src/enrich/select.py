from __future__ import annotations

import json
from typing import Dict, List
from urllib.parse import urlparse

from src.config import INDUSTRIAL_SIGNALS, DEPRIORITIZE_SIGNALS

# Prova a usare il client OpenAI solo se già disponibile nel tuo progetto.
# Se non è disponibile o fallisce, il codice usa fallback deterministic.
try:
    from openai import OpenAI
except Exception:
    OpenAI = None


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


def _deterministic_is_deprioritized(event: Dict) -> bool:
    blob = _blob(event)
    has_negative = _has_any(blob, DEPRIORITIZE_SIGNALS)
    has_positive = _has_any(blob, INDUSTRIAL_SIGNALS)
    return has_negative and not has_positive


def _deterministic_is_supply_base_core(event: Dict) -> bool:
    blob = _blob(event)

    if _has_any(blob, INDUSTRIAL_SIGNALS):
        return True

    try:
        score = int(event.get("score") or 0)
    except Exception:
        score = 0

    return score >= 70


def _build_ai_prompt(event: Dict) -> str:
    title = event.get("title", "") or ""
    text = event.get("summary_seed", "") or ""
    score = event.get("score", 0)

    return f"""
You are selecting events for a weekly briefing for a COO / industrial strategy leader
at an automotive supplier.

The briefing should prioritize:
- supplier economics
- sourcing and localisation
- plant footprint and industrial capacity
- industrialisation timing
- electronics / PCBA / semiconductor exposure
- OEM vertical integration
- trade barriers / regulation
- M&A / supplier distress

Deprioritize:
- product reviews
- consumer vehicle launches unless there is clear sourcing/industrial impact
- brand/image PR
- motorsport unless it has supplier or industrial implications
- generic market chatter without supply-base implications

Evaluate this event and return JSON only with this schema:
{{
  "include": true,
  "is_noise": false,
  "supplier_relevance": 0,
  "managerial_relevance": 0,
  "priority": 0,
  "reason": "max 25 words"
}}

Rules:
- include=true only if this belongs in a supplier-focused executive brief
- supplier_relevance, managerial_relevance, priority must be integers from 0 to 5
- be strict

Event:
Title: {title}
Score: {score}
Text: {text[:2500]}
""".strip()


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _ai_assess_event(event: Dict, model: str = "gpt-5.4-mini") -> Dict:
    """
    AI assessment with safe fallback.
    If anything fails, returns deterministic-style fallback assessment.
    """
    fallback = {
        "include": (
            (not _deterministic_is_deprioritized(event))
            and _deterministic_is_supply_base_core(event)
        ),
        "is_noise": _deterministic_is_deprioritized(event),
        "supplier_relevance": 4 if _deterministic_is_supply_base_core(event) else 1,
        "managerial_relevance": 4 if _deterministic_is_supply_base_core(event) else 1,
        "priority": min(5, max(0, _safe_int(event.get("score"), 0) // 20)),
        "reason": "deterministic fallback",
    }

    if OpenAI is None:
        return fallback

    try:
        client = OpenAI()
        prompt = _build_ai_prompt(event)

        resp = client.responses.create(
            model=model,
            input=prompt,
        )

        text = getattr(resp, "output_text", "") or ""
        data = json.loads(text)

        return {
            "include": bool(data.get("include", fallback["include"])),
            "is_noise": bool(data.get("is_noise", fallback["is_noise"])),
            "supplier_relevance": max(0, min(5, _safe_int(data.get("supplier_relevance"), fallback["supplier_relevance"]))),
            "managerial_relevance": max(0, min(5, _safe_int(data.get("managerial_relevance"), fallback["managerial_relevance"]))),
            "priority": max(0, min(5, _safe_int(data.get("priority"), fallback["priority"]))),
            "reason": (data.get("reason") or fallback["reason"])[:120],
        }
    except Exception as e:
        print(f"[SELECT AI WARNING] fallback for '{event.get('title', '')}': {e}")
        return fallback


def _is_deprioritized(event: Dict) -> bool:
    """
    AI-first deprioritization with deterministic fallback.
    """
    assessment = event.get("_ai_assessment")
    if assessment is None:
        assessment = _ai_assess_event(event)
        event["_ai_assessment"] = assessment
    return bool(assessment.get("is_noise", False))


def _is_supply_base_core(event: Dict) -> bool:
    """
    AI-first inclusion with deterministic fallback.
    """
    assessment = event.get("_ai_assessment")
    if assessment is None:
        assessment = _ai_assess_event(event)
        event["_ai_assessment"] = assessment
    return bool(assessment.get("include", False))


def select_events(
    events: List[Dict],
    *,
    max_total: int = 10,
    max_per_domain: int = 3,
) -> List[Dict]:
    """
    AI-assisted selection of the best supplier-relevant events.
    Keeps the same public interface so main.py does not need changes.
    """
    # 1) filter out weak / noisy items
    filtered: List[Dict] = []
    for event in events:
        if _is_deprioritized(event):
            continue
        if _is_supply_base_core(event):
            filtered.append(event)

    print("\n===== FILTERED EVENTS =====\n")
    for i, z in enumerate(filtered):
        a = z.get("_ai_assessment", {})
        print(
            f"{i+1}. {z.get('title','NO TITLE')} "
            f"| include={a.get('include')} noise={a.get('is_noise')} "
            f"| prio={a.get('priority')} sup={a.get('supplier_relevance')} mgr={a.get('managerial_relevance')}"
        )
    print("\n===== END FILTERED =====\n")

    # 2) sort by AI priority first, then supplier/managerial relevance,
    #    then original score, then publication date
    filtered.sort(
        key=lambda e: (
            _safe_int(e.get("_ai_assessment", {}).get("priority"), 0),
            _safe_int(e.get("_ai_assessment", {}).get("supplier_relevance"), 0),
            _safe_int(e.get("_ai_assessment", {}).get("managerial_relevance"), 0),
            _safe_int(e.get("score"), 0),
            e.get("published_at") or "",
        ),
        reverse=True,
    )

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

    # remove internal debug/AI helper field before returning
    for event in selected:
        event.pop("_ai_assessment", None)

    return selected
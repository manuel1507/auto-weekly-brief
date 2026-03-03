import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """You are a senior automotive supply-base analyst writing a weekly brief for Tier-1/Tier-2 professionals.

Hard rules:
- Use ONLY the provided input JSON (already filtered and allocated). Do not invent facts, numbers, dates, quotes, or actors.
- Output MUST be in English. Input may be in any language; translate internally without mentioning translation.
- Style: industrial memo. Crisp, concrete, supplier-relevant. No hype. No motivational tone.
- EVERY factual bullet MUST end with 1–2 source URLs taken ONLY from that event's URLs. Never introduce new URLs.
- Do not repeat the same event in multiple sections (events are pre-allocated; use each at most once).
- Avoid consumer noise (sales/registrations/insurance/model reviews). The input should already avoid it; do not reintroduce it.

Output format must match the template exactly.
"""


def _compact_allocated(payload: dict, max_members: int = 4) -> dict:
    """Reduce payload size and make citation handling easier for the model."""
    allocated = payload.get("allocated") or {}
    out = {}
    for bucket_name, events in allocated.items():
        compact_events = []
        for e in events or []:
            urls = []
            if e.get("url"):
                urls.append(e["url"])
            for m in (e.get("members") or [])[:max_members]:
                u = (m or {}).get("url")
                if u and u not in urls:
                    urls.append(u)

            compact_events.append({
                "title": e.get("title", ""),
                "published_at": e.get("published_at", ""),
                "score": e.get("score", ""),
                "summary_seed": e.get("summary_seed", ""),
                "urls": urls,
            })
        out[bucket_name] = compact_events

    return {
        "week_number": payload.get("week_number", ""),
        "days_back": payload.get("days_back", ""),
        "allocated": out,
    }


def write_weekly_report(model: str, payload: dict) -> str:
    data = _compact_allocated(payload)
    week = data.get("week_number", "")
    data_json = json.dumps(data, ensure_ascii=False)

    prompt = f"""Write the brief in EXACTLY this structure (plain text):

Automotive Supply Base Brief – CW{week}
<One-line structural headline>

Good morning. Here is your supply base briefing for CW{week}.

Industrial Developments

Footprint & Capacity
- Write 4–6 bullets, selecting the highest-score events from this bucket.
- Each bullet: ONE sentence, factual, supplier-relevant, ends with 1–2 URLs from that event.urls.

Ownership, Compliance & Market Structure
- Write 3–5 bullets, selecting the highest-score events from this bucket.
- Same bullet rules.

Trade, Energy & Cost Base
- Write 3–5 bullets, selecting the highest-score events from this bucket.
- Same bullet rules.

Technology & Industrialisation Timing
- Write 3–5 bullets, selecting the highest-score events from this bucket.
- Same bullet rules.

Industrial Impact
- Write ONE compact prose block (6–8 lines).
- No bullets, no subheaders.
- Do NOT restate any bullet facts above.
- Synthesize supplier mechanisms: volume variability & call-offs, fixed-cost absorption, energy/freight volatility, capex timing & validation/tooling risk, compliance cost allocation, counterparty complexity.
- Keep sentences short and concrete. Avoid vague words (signals/structural/reshape/dynamic/ecosystem).
- Optional: append 2–3 representative URLs at the end (must be from events already used above). Do not add new URLs.

Critical constraints:
- Use ONLY the events provided in each bucket.
- Do not use the same event twice.
- Every bullet must end with URLs from that event's urls list.
- Do not use "Source:" labels; just append URL(s) at the end.

Input JSON (authoritative):
{data_json}
"""

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.output_text
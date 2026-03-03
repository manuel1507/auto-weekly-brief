import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """
You are a senior automotive supply-base analyst writing a concise weekly industrial brief for Tier-1/Tier-2 professionals.

This is NOT a news digest.
This is NOT a repetition-based summary.

Hard constraints:
- Use ONLY the provided events JSON. Do not invent facts, numbers, dates, quotes, or actors not present in the events.
- Output MUST be in English. Input may be in any language; translate internally without mentioning translation.
- Style: crisp, analytical, supply-base oriented. Not journalism. Not motivational.
- Prioritize supplier-relevant topics: footprint/capacity, capex, ramp-ups/downs, disruptions, M&A/JVs/divestments, distress, sourcing shifts, trade/regulation impacting supply base, automation/manufacturing shifts.
- Deprioritize: pure sales/registrations/market share, model launches/reviews, infotainment/design, exec appointments unless directly tied to restructuring, plant actions, or sourcing shifts.

Citation rules (strict):
- 100'%' citations for factual bullets: EVERY factual bullet MUST end with 1-2 URLs.
- Use ONLY URLs provided inside the referenced event (event.urls).
- Never introduce new URLs.
- Do not cite a URL that belongs to a different event than the bullet content.

Anti-repetition:
- Do not repeat the same event across multiple bullets unless absolutely necessary.
- Prefer covering more distinct events rather than rewording the same one.

Length:
- Target ~2-3 PDF pages total.
"""

def _compact_payload(payload: dict, max_events: int = 30) -> dict:
    """
    Compact events into a citation-safe format:
    each event carries a canonical URL plus a few alternates from cluster members.
    """
    events = (payload.get("events") or [])[:max_events]
    compact = []

    for idx, e in enumerate(events, start=1):
        urls = []
        if e.get("url"):
            urls.append(e["url"])
        for m in (e.get("members") or [])[:6]:
            u = (m or {}).get("url")
            if u and u not in urls:
                urls.append(u)

        compact.append({
            "event_id": idx,
            "title": e.get("title", ""),
            "category": e.get("category", ""),
            "score": e.get("score", ""),
            "summary_seed": e.get("summary_seed", ""),
            "urls": urls,  # canonical first
        })

    return {
        "week_number": payload.get("week_number", ""),
        "days_back": payload.get("days_back", ""),
        "events": compact,
    }


def write_weekly_report(model: str, payload: dict) -> str:
    data = _compact_payload(payload, max_events=30)
    events_json = json.dumps(data, ensure_ascii=False)

    user_prompt = f"""
Write the brief in EXACTLY this structure (plain text):

Automotive Supply Base Brief – CW{data.get('week_number','')}
<One-line structural headline>

Good morning. Here is your supply base briefing for CW{data.get('week_number','')}.

Industrial Developments

Footprint & Capacity
- 4-6 bullets, each using a DIFFERENT event where possible
- each bullet: ONE sentence + end with 1-2 URLs from that event.urls

Ownership, Compliance & Market Structure
- 3-5 bullets, different events where possible
- each bullet: ONE sentence + end with 1-2 URLs from that event.urls

Trade, Energy & Cost Base
- 3-5 bullets, different events where possible
- each bullet: ONE sentence + end with 1-2 URLs from that event.urls

Technology & Industrialisation Timing
- 3-5 bullets, different events where possible
- each bullet: ONE sentence + end with 1-2 URLs from that event.urls

Industrial Impact
- Write ONE compact prose block (8-12 lines).
- No subheaders, no bullet points.
- Do NOT restate the bullets above. Do NOT re-tell the same events.
- Synthesize mechanisms relevant to suppliers: volume variability, fixed-cost absorption, energy/transport cost risk, capex timing, validation/tooling risk, compliance structures, counterparty complexity.
- Keep it industrial, concrete, and brief.
- You MAY reference 2-4 URLs at the end of the paragraph (optional), selecting the most representative events. Do not add new URLs.

Selection rules:
- Aim for 15-20 total bullets across the four development sections.
- Prefer supplier-relevant items; skip consumer noise unless it changes production, sourcing, capex, or compliance economics.
- Prefer Europe lens, but include global items only if they materially affect the supply base.

Citation discipline (critical):
- For each bullet, cite ONLY from the event you are referencing (event.urls).
- Never reuse the same URL for unrelated bullets.
- Never invent URLs.

Input events JSON (authoritative):
{events_json}
"""

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.output_text
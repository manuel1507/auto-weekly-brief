import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """
You are a senior automotive supply-base analyst writing a concise weekly industrial brief.

This is NOT a news digest.
This is NOT a repetition-based summary.

Hard constraints:

- Use ONLY the provided events JSON. Do not invent facts, numbers, dates, quotes, or actors not present in the events.
- Do NOT invent facts.
- Output MUST be in English. Input may be in any language; translate internally without mentioning translation.
- Every factual bullet must end with at least one URL.
- Style: crisp, analytical, supply-base oriented. Not journalism. Not motivational.
- Prioritize supplier-relevant topics: footprint/capacity, capex, ramp-ups/downs, disruptions, M&A/JVs/divestments, distress, sourcing shifts, trade/regulation impacting supply base, automation/manufacturing shifts.
- Deprioritize: pure sales/registrations/market share, model launches/reviews, infotainment/design, exec appointments unless directly tied to restructuring, plant actions, or sourcing shifts.
- 100'% 'citations: EVERY line that makes a factual claim must end with at least one source URL.
- Use ONLY URLs provided inside the referenced event.
- Each event may be described ONLY ONCE in the entire memo.
   - Once an event is used in Executive Signals or Industrial Developments,
     it must NOT be repeated verbatim in other sections.
   - Implications must be cross-event, structural, and NOT repeat event descriptions.
- Avoid redundancy across sections.
- Focus strictly on supplier-relevant structural developments.
- Keep total length tight (2-3 pages max).
- Citation discipline: For each item, cite ONLY URLs from that event's provided 'urls'. Never cite a URL from a different event. Never introduce new URLs.

"""

def _compact_payload(payload: dict, max_events: int = 25) -> dict:
    events = (payload.get("events") or [])[:max_events]
    compact = []

    for idx, e in enumerate(events):
        urls = []
        if e.get("url"):
            urls.append(e["url"])
        for m in (e.get("members") or [])[:4]:
            u = (m or {}).get("url")
            if u and u not in urls:
                urls.append(u)

        compact.append({
            "event_id": idx + 1,
            "title": e.get("title", ""),
            "summary_seed": e.get("summary_seed", ""),
            "urls": urls,
        })

    return {
        "week_number": payload.get("week_number", ""),
        "events": compact,
    }


def write_weekly_report(model: str, payload: dict) -> str:
    data = _compact_payload(payload)
    events_json = json.dumps(data, ensure_ascii=False)

    user_prompt = f"""
Write the memo in EXACTLY this structure:

Automotive Supply Base Brief – CW{data.get('week_number','')}
<One-line headline>

Good morning. Here is your supply base briefing for CW{data.get('week_number','')}.

This week signals a structural shift in European automotive power dynamics:
<Exactly 5 signal lines. Each based on a DIFFERENT event. Each line ends with URL.>

Strategic Take
<8-12 lines.
No event repetition.
Synthesize patterns across the 5 selected signals.
Do NOT restate facts already written.
No URLs in this section. This is analytical.>

Industrial Developments

Battery & Powertrain
<2-3 bullets, each using a DIFFERENT unused event>

Ownership & M&A
<2-3 bullets, different unused events>

Trade & Policy
<2-3 bullets, different unused events>

Automation & Manufacturing
<2-3 bullets, different unused events>

What This Means for Tier-1 & Tier-2 Suppliers

Margin Structure
<2-3 bullets. No direct event repetition. Structural mechanisms only. No URLs.>

Footprint
<2-3 bullets. Cross-event implications only. No URLs.>

Ownership Risk
<23 bullets. Cross-event implications only. No URLs.>

Capital Allocation
<2-3 bullets. Cross-event implications only. No URLs.>

Critical rules:
- An event can appear ONLY ONCE in factual sections.
- Do NOT repeat Berlin in 4 sections.
- Do NOT restate the same solid-state claim twice.
- Implications must generalize patterns, not restate events.
- If insufficient events fit a category, write fewer bullets.
- Prioritize European industrial impact.

Input events:
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
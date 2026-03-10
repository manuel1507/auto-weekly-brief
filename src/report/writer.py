import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """
You are a senior automotive supply-base analyst writing a short weekly LinkedIn-ready brief for professionals in the automotive industry.

Audience:
- Tier-1 and Tier-2 managers
- operations leaders
- purchasing leaders
- strategy / industrial footprint professionals

Hard rules:
- Use ONLY the provided events JSON.
- Do not invent facts, numbers, dates, quotes, or actors.
- Output MUST be in English.
- Input may be in any language; translate internally without mentioning translation.
- Keep the tone professional, sharp, and executive.
- This is not a long memo and not a newspaper article.
- Focus on supplier-relevant developments only.

Priority topics:
- plant openings / closures / utilisation / ramp-up / capacity
- supplier distress / restructuring / M&A / JV
- sourcing shifts
- capex / tooling / validation / industrialisation timing
- tariffs / regulation / compliance economics
- manufacturing automation / robotics / electronics / batteries

Deprioritize or exclude:
- registrations / market share / consumer sales
- insurance and consumer-affordability stories
- model launches / facelifts / design / infotainment
- awards / charity / generic PR
- executive appointments unless tied to operational or sourcing impact

Citation discipline:
- Every bullet that contains a factual statement MUST end with 1–2 URLs.
- Use ONLY URLs from the event being referenced.
- Never introduce new URLs.
- Never cite a URL from a different event.

Anti-repetition:
- Do not repeat the same event in multiple bullets.
- Prefer breadth over rewording the same point.
"""

def _compact_payload(payload: dict, max_events: int = 10) -> dict:
    events = (payload.get("events") or [])[:max_events]
    compact = []

    for idx, event in enumerate(events, start=1):
        urls = []
        if event.get("url"):
            urls.append(event["url"])

        for member in (event.get("members") or [])[:4]:
            u = (member or {}).get("url")
            if u and u not in urls:
                urls.append(u)

        compact.append({
            "event_id": idx,
            "title": event.get("title", ""),
            "category": event.get("category", ""),
            "score": event.get("score", ""),
            "summary_seed": event.get("summary_seed", ""),
            "urls": urls,
        })

    return {
        "week_number": payload.get("week_number", ""),
        "days_back": payload.get("days_back", ""),
        "events": compact,
    }


def write_weekly_report(model: str, payload: dict) -> str:
    data = _compact_payload(payload, max_events=10)
    week = data.get("week_number", "")
    events_json = json.dumps(data, ensure_ascii=False)

    prompt = f"""
Write the output in EXACTLY this structure (plain text, no markdown tables):

Automotive Supply Base Brief – CW{week}
<One-line headline>

Good morning. Here is your supply base briefing for CW{week}.

Top supply-base signals

- Write 8–10 bullets, using the strongest events from the input.
- Use each event at most once.
- Each bullet must:
  1. state the fact,
  2. explain in the same sentence why it matters for Tier-1 / Tier-2 suppliers,
  3. end with 1–2 URLs from that event.urls.
- Keep each bullet concise and readable for LinkedIn.
- Do not create sub-sections.

Bottom line

- Write one short closing paragraph (4–6 lines).
- No bullets in this section.
- Synthesize what the selected events mean for suppliers.
- Focus on practical industrial implications: localisation pressure, capex discipline, supplier risk, validation timing, automation intensity, trade friction.
- Do NOT restate the bullets one by one.
- URLs are optional here; if used, append at most 2 representative URLs at the end, chosen from the events already used above.

Additional rules:
- If the input has fewer than 8 strong events, write fewer bullets rather than adding weak ones.
- Avoid filler words and vague abstractions.
- Avoid generic phrases like "this signals a structural shift" unless followed by a concrete supplier implication.
- Do not mention consumers, unless the event clearly changes production, sourcing, or supplier economics.

Input events JSON (authoritative):
{events_json}
"""

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )

    return resp.output_text
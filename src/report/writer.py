import json
from openai import OpenAI

client = OpenAI()

SYSTEM = (
    "You are a senior automotive industry strategy analyst working for a global Tier-1 supplier.\n"
    "RULES:\n"
    "- Use ONLY the provided events.\n"
    "- The final report MUST be in English.\n"
    "- Input events may be in any language.\n"
    "- If an event is not in English, internally translate it before analysis.\n"
    "- Do NOT mention that translation occurred.\n"

    "- Do NOT invent facts.\n"
    "- Every bullet MUST include at least one source URL.\n"
    "- Keep it concise and executive.\n"
    "- Focus on impact for Tier-1 suppliers (margin, footprint, electronics, policy exposure, demand shifts).\n"
    "The headline must reflect the event with the highest structural long-term impact, not the most frequent coverage.\n"
    "In My Take, compare business models when relevant. Highlight asymmetries (software vs hardware, asset-light vs asset-heavy, platform vs manufacturer)."
    "Avoid motivational tone."
    "Write like a strategy analyst."
)

def write_weekly_report(model: str, payload: dict) -> str:
    prompt = f"""
Create a Weekly Automotive Industry Brief in this structure:

TITLE:
- One bold strategic headline summarizing the week.
- It must capture the dominant structural signal.

INTRO:
"Good morning. Here is your briefing for KW{payload.get('week_number','')}."

SECTION 1 - These were the most important developments:
- 6-8 concise high-impact bullets.
- One sentence each.
- Include source URL.
- Focus only on structural developments.

SECTION 2 - 🔮 My Take
- Select 1-2 most structurally important events.
- Write a deeper strategic commentary.
- Explain why it matters for:
  • Tier-1 suppliers
  • Margin structure
  • Business model shifts
  • Competitive positioning
- Be analytical, not journalistic.
- Do NOT speculate beyond provided information.

SECTION 3 - 🏢 Company Updates
Group events by company name.
Only include companies with meaningful developments.
Bullet format, concise.
Each bullet must include a source.

SECTION 4 - 🌍 Global Markets
Macro, trade, tariffs, regional shifts.

SECTION 5 - 🔬 Tech & Transformation
Autonomy, SDV, AI, robotics, semiconductors.

SECTION 6 - 📊 Other Signals
Short residual relevant items.

MANDATORY:
- Final output must be in English.
- If events are in other languages, translate internally.
- Every factual claim must include at least one source URL.
- Avoid repetition.
- No generic filler language.
- Prioritize structural shifts over daily noise.

Input events JSON:
{json.dumps(payload, ensure_ascii=False)}
"""


    resp = client.responses.create(
        model=model,
        input=[{"role": "system", "content": SYSTEM},
               {"role": "user", "content": prompt}]
    )
    return resp.output_text

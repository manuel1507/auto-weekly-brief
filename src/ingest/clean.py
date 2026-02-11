import html
import re
import unicodedata

# Common typography → plain ASCII (safe for PDF + consistent)
_PUNCT_TRANSLATION = str.maketrans({
    # Single quotes / apostrophes
    "\u2018": "'",  # ‘
    "\u2019": "'",  # ’
    "\u201A": "'",  # ‚
    "\u2032": "'",  # ′
    "\u02BC": "'",  # ʼ
    "\uFF07": "'",  # ＇

    # Double quotes
    "\u201C": '"',  # “
    "\u201D": '"',  # ”
    "\u201E": '"',  # „
    "\u2033": '"',  # ″
    "\uFF02": '"',  # ＂

    # Dashes / hyphens
    "\u2010": "-",  # ‐
    "\u2011": "-",  # non-breaking hyphen
    "\u2012": "-",  # ‒
    "\u2013": "-",  # –
    "\u2014": "-",  # —
    "\u2212": "-",  # − (minus sign)
    "\uFE63": "-",  # ﹣
    "\uFF0D": "-",  # －

    # Ellipsis
    "\u2026": "...",  # …

    # Spaces / invisibles that often break PDFs or URLs
    "\u00A0": " ",   # NBSP
    "\u2007": " ",   # figure space
    "\u202F": " ",   # narrow no-break space
    "\u2009": " ",   # thin space
    "\u200A": " ",   # hair space
    "\u2060": "",    # word joiner
    "\u200B": "",    # zero width space
    "\u200C": "",    # zero width non-joiner
    "\u200D": "",    # zero width joiner
    "\uFEFF": "",    # BOM / zero width no-break space
})

_NUM_ENTITY_RE = re.compile(r"&#(\d+);")
_HEX_ENTITY_RE = re.compile(r"&#x([0-9a-fA-F]+);")

def _decode_numeric_entities(s: str) -> str:
    def dec(m):
        try:
            return chr(int(m.group(1)))
        except Exception:
            return m.group(0)

    def hexdec(m):
        try:
            return chr(int(m.group(1), 16))
        except Exception:
            return m.group(0)

    s = _HEX_ENTITY_RE.sub(hexdec, s)
    s = _NUM_ENTITY_RE.sub(dec, s)
    return s

def _strip_problem_unicode(s: str) -> str:
    """
    Remove characters that commonly show as squares or weird glyphs in PDFs:
    - Unicode categories starting with 'C' (control/format/surrogate/private/unassigned)
    - explicit noncharacters U+FFFE/U+FFFF
    Keep \n and \t.
    """
    out = []
    for ch in s:
        if ch in ("\n", "\t"):
            out.append(ch)
            continue

        o = ord(ch)
        if o in (0xFFFE, 0xFFFF):
            continue

        cat = unicodedata.category(ch)
        if cat and cat[0] == "C":
            # Drop Cc, Cf, Cs, Co, Cn
            continue

        out.append(ch)
    return "".join(out)

def clean_text(s: str) -> str:
    """
    Robust cleaner for RSS / HTML / LLM output.

    - Decodes HTML entities (handles double-escaped like &amp;#039;)
    - Normalizes Unicode (NFKC)
    - Converts typographic quotes/dashes to plain ASCII
    - Removes invisible/control chars that break PDF rendering or URLs
    - Normalizes whitespace while preserving paragraphs
    """
    if not s:
        return s

    # 1) Decode HTML/XML entities (twice catches &amp;#039; -> &#039; -> ')
    s = html.unescape(s)
    s = html.unescape(s)

    # 2) Decode any leftover numeric entities
    s = _decode_numeric_entities(s)

    # 3) Unicode normalization
    s = unicodedata.normalize("NFKC", s)

    # 4) Normalize punctuation and remove common invisibles
    s = s.translate(_PUNCT_TRANSLATION)

    # 5) Strip remaining control/format/private/unassigned chars (PDF killers)
    s = _strip_problem_unicode(s)

    # 6) Normalize line whitespace but keep paragraphs
    # - compress internal spaces/tabs per line
    # - keep max 2 consecutive newlines
    s = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in s.splitlines())
    s = re.sub(r"\n{3,}", "\n\n", s).strip()

    return s

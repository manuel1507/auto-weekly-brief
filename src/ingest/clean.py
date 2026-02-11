import html
import re
import unicodedata

# Translation map for common “typographic” punctuation to plain ASCII equivalents
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
    "\u2011": "-",  # -
    "\u2012": "-",  # ‒
    "\u2013": "-",  # –
    "\u2014": "-",  # —
    "\u2212": "-",  # − (minus)

    # Ellipsis
    "\u2026": "...",  # …

    # Spaces
    "\u00A0": " ",  # NBSP
    "\u2007": " ",  # figure space
    "\u202F": " ",  # narrow no-break space
    "\u2009": " ",  # thin space
    "\u200A": " ",  # hair space
    "\u2060": "",   # word joiner (invisible)
    "\uFEFF": "",   # BOM / zero width no-break space
})

_NUM_ENTITY_RE = re.compile(r"&#(\d+);")
_HEX_ENTITY_RE = re.compile(r"&#x([0-9a-fA-F]+);")

def _decode_numeric_entities(s: str) -> str:
    # Decode any leftover numeric entities that html.unescape didn't catch for some reason
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

def clean_text(s: str) -> str:
    """
    Cleans RSS/HTML text robustly:
    - Decodes HTML entities (handles double-escaped like &amp;#039;)
    - Normalizes common typographic quotes/dashes/ellipsis to ASCII
    - Normalizes Unicode (NFKC) to reduce odd variants
    - Removes control chars and normalizes whitespace
    """
    if not s:
        return s

    # 1) HTML/XML entity decoding (twice catches &amp;#039; -> &#039; -> ')
    s = html.unescape(s)
    s = html.unescape(s)

    # 2) Decode any stragglers (rare but cheap)
    s = _decode_numeric_entities(s)

    # 3) Unicode normalization
    s = unicodedata.normalize("NFKC", s)

    # 4) Normalize punctuation and spaces
    s = s.translate(_PUNCT_TRANSLATION)

    # 5) Remove control characters except \n and \t (keep paragraph structure if present)
    s = "".join(ch for ch in s if ch == "\n" or ch == "\t" or (ord(ch) >= 32 and ord(ch) != 127))

    # 6) Normalize whitespace (keep newlines; compress spaces on each line)
    s = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in s.splitlines())
    s = re.sub(r"\n{3,}", "\n\n", s).strip()

    return s

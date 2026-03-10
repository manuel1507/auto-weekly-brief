from dataclasses import dataclass
from typing import List

@dataclass
class Settings:
    days_back: int = 7
    max_items_per_feed: int = 20
    # Cost-effective defaults; adjust later
    llm_model: str = "gpt-5-mini"
    embed_model: str = "text-embedding-3-small"
    dedup_threshold: float = 0.86

    # Target output size for the brief (15–20 events total)
    max_events_in_report: int = 50

    # Limit how many final events can come from the same publisher domain
    max_per_domain: int = 3


# Start with RSS only (stable). Add your own feeds.
RSS_FEEDS: List[str] = [
  # Examples (replace with your chosen feeds)
  #"https://www.autonews.com/rss.xml"
  #"https://europe.autonews.com/rss.xml",
  "https://www.quattroruote.it/content/quattroruote/it/listino/feeds/newsRss/feed.xml",
  #https://www.automotiveworld.com/feed/",
  #"https://www.alvolante.it/rss.xml",
  #"https://www.motor1.com/rss/news/all/",
  #"https://cnevpost.com/feed/",
  #"https://auto.economictimes.indiatimes.com/rss/topstories",
  #"https://www.just-auto.com/feed/",
  #"https://www.autonews.com/arc/outboundfeeds/sitemap-news/",
  "https://www.ilsole24ore.com/rss/motori--mercato-e-industria.xml",
  #"https://www.ilsole24ore.com/rss/motori--auto.xml",
  "https://www.ilsole24ore.com/rss/motori--mobilita-e-tech.xml",
  #"https://www.wardsauto.com/rss.xml",
  #"https://www.automotivelogistics.media/rss",
  #"https://www.automotivemanufacturingsolutions.com/rss",
  #"https://www.supplychainbrain.com/rss/topic/auto",
  #"https://www.eetimes.com/category/automotive/feed/",
  #"https://www.electronicsweekly.com/automotive/feed",
  #"https://semiengineering.com/category/automotive/feed/",
  "https://feeds.highgearmedia.com/?sites=MotorAuthority&tags=news",
  "https://www.einnews.com/rss/Ivz9I5o09oVD3CVE",
  "https://www.clepa.eu/feed/",
  "https://media.mercedes-benz.it/tagfeed/it/tags/corporate,business__news",
  "https://www.press.bmwgroup.com/global/rss",
  "https://www.automoto.it/rss/news.xml",
  "https://it.motor1.com/rss/category/attualita/",
  "https://it.motor1.com/rss/category/market/",
  #"https://www.volkswagen-newsroom.com/en/rss.xml",
  "https://www.stellantis.com/en/news/press-releases.rss.xml",
]


# Tier-1 lens keywords: used for scoring and section routing
# NOTE: intentionally de-emphasize sales/model/PR noise.
KEYWORDS = {
    # Keep but low weight in rank.py (or remove entirely if you want)
    "oem_demand": ["inventory", "mix"],

    # Supplier-relevant
    "suppliers": ["supplier", "contract", "tier-1", "tier 1", "tier-2", "tier 2", "sourcing", "rfq", "quote"],

    "footprint_ops": [
        "plant", "factory", "capacity", "utilization", "shutdown", "closure",
        "expansion", "localization", "nearshoring", "ramp-up", "ramp up", "ramp down",
        "new facility", "line", "shift", "output", "production"
    ],

    "policy_trade": ["tariff", "subsidy", "regulation", "emissions", "homologation", "ban", "duty", "compliance"],

    "quality_recalls": ["recall", "defect", "safety", "campaign", "investigation"],
}


# Termini che indicano forte rilevanza industriale (produzione/footprint/M&A/supply chain)
INDUSTRIAL_SIGNALS = [
    # footprint/capacity
    "plant", "factory", "facility", "site", "greenfield", "brownfield",
    "capacity", "utilization", "throughput", "ramp-up", "ramp up", "ramp down",
    "shift", "line", "tooling",
    "shutdown", "closure", "close", "halt", "suspend",
    "production", "output", "assembly",
    "capex", "investment", "expansion", "new facility",

    # restructuring / distress
    "layoff", "layoffs", "job cuts", "redundancies",
    "bankruptcy", "insolvency", "restructuring", "administration",

    # ownership
    "acquire", "acquisition", "merger", "m&a", "takeover", "divest", "spin-off",
    "joint venture", "jv", "stake", "sell", "sale",

    # supply base
    "supplier", "tier 1", "tier-1", "tier 2", "tier-2", "sourcing", "rfq",

    # electronics / manufacturing
    "semiconductor", "chip", "pcb", "pcba", "wiring harness", "connector",

    # batteries / materials (only when industrialisation/timing is relevant)
    "battery cell", "cathode", "anode", "lithium", "rare earth"
]


# Termini tipici di news meno utili (vendite / modello / PR)
DEPRIORITIZE_SIGNALS = [
    "sales", "registrations", "deliveries", "market share",
    "new model", "facelift", "refresh", "trim", "variant",
    "first drive", "test drive", "review",
    "design", "interior", "infotainment",
    "appointed", "named", "joins as", "new ceo", "new cto", "board",
    "award", "nomination",
    "insurance", "assicurazione", "polizza", "premi",
]
from dataclasses import dataclass
from typing import List

@dataclass
class Settings:
    days_back: int = 7
    max_items_per_feed: int = 5
    # Cost-effective defaults; adjust later
    llm_model: str = "gpt-5-mini"
    embed_model: str = "text-embedding-3-small"
    dedup_threshold: float = 0.86
    max_events_in_report: int = 80

# Start with RSS only (stable). Add your own feeds.
RSS_FEEDS: List[str] = [
    # Examples (replace with your chosen feeds)
  #"https://www.autonews.com/rss.xml"
  #"https://europe.autonews.com/rss.xml",
  "https://www.quattroruote.it/content/quattroruote/it/listino/feeds/newsRss/feed.xml",
  "https://www.automotiveworld.com/feed/",
  #"https://www.alvolante.it/rss.xml",
  #"https://www.motor1.com/rss/news/all/",
  #"https://cnevpost.com/feed/",
  #"https://auto.economictimes.indiatimes.com/rss/topstories",
  #"https://www.just-auto.com/feed/",
  #"https://www.autonews.com/arc/outboundfeeds/sitemap-news/",
  "https://www.ilsole24ore.com/rss/motori--mercato-e-industria.xml",
  #"https://www.ilsole24ore.com/rss/motori--auto.xml",
  #"https://www.ilsole24ore.com/rss/motori--mobilita-e-tech.xml",
  #"https://www.wardsauto.com/rss.xml",
  #"https://www.automotivelogistics.media/rss",
  #"https://www.automotivemanufacturingsolutions.com/rss",
  #"https://www.supplychainbrain.com/rss/topic/auto",
  #"https://www.eetimes.com/category/automotive/feed/",
  #"https://www.electronicsweekly.com/automotive/feed",
  #"https://semiengineering.com/category/automotive/feed/",
  #"https://www.sae.org/rss",
  #"https://www.press.bmwgroup.com/global/rss",
  #"https://www.volkswagen-newsroom.com/en/rss.xml",
  #"https://www.media.stellantis.com/rss",
]

# Tier-1 lens keywords: used for scoring and section routing
KEYWORDS = {
    "oem_demand": ["sales", "deliveries", "pricing", "price cut", "inventory", "mix", "launch"],
    "suppliers": ["supplier", "contract", "award", "tier-1", "tier 1", "tier-2", "tier 2", "quote"],
    "footprint_ops": ["plant", "factory", "capacity", "shutdown", "closure", "expansion", "localization", "nearshoring"],
    #"ev_battery": ["EV", "battery", "cell", "cathode", "anode", "lithium", "LFP", "NMC", "gigafactory", "recycling"],
    #"electronics_sdv": ["ECU", "E/E", "chip", "semiconductor", "ADAS", "software-defined", "SDV", "cybersecurity"],
    "policy_trade": ["tariff", "subsidy", "regulation", "emissions", "homologation", "ban", "duty"],
    "quality_recalls": ["recall", "defect", "safety", "campaign", "investigation"],
}

# Notizie che vogliamo privilegiare per un brief Tier-1 (produzione/footprint/M&A/supply chain)
CORE_CATEGORIES = {
    "FOOTPRINT_CAPACITY",
    "M&A",
    "RESTRUCTURING",
    "SUPPLY_CHAIN",
    "REGULATION_SUPPLY"
}

# Termini che indicano forte rilevanza industriale (aumenti capacità, chiusure, investimenti, ecc.)
INDUSTRIAL_SIGNALS = [
    "plant", "factory", "facility", "site", "greenfield", "brownfield",
    "capacity", "ramp-up", "ramp up", "shift", "line", "tooling",
    "shutdown", "closure", "close", "halt", "suspend",
    "layoff", "layoffs", "job cuts", "redundancies",
    "capex", "investment", "expansion", "new facility", "production",
    "bankruptcy", "insolvency", "restructuring", "administration",
    "acquire", "acquisition", "merger", "m&a", "takeover", "divest", "spin-off", "joint venture", "jv",
    "supplier", "tier 1", "tier-1", "tier 2", "tier-2", "sourcing", "award", "nomination",
    "semiconductor", "chip", "pcb", "pcba", "wiring harness", "connector",
    "battery cell", "cathode", "anode", "lithium", "rare earth"
]

# Termini tipici di news meno utili per te (vendite / modello / PR)
DEPRIORITIZE_SIGNALS = [
    "sales", "registrations", "deliveries", "market share",
    "new model", "facelift", "refresh", "trim", "variant",
    "first drive", "test drive", "review",
    "design", "interior", "infotainment",
    "appointed", "named", "joins as", "new ceo", "new cto", "board"
]

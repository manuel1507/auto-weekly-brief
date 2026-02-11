import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm

def _escape(s: str) -> str:
    # Escape minimo per Paragraph (evita che < > & rompano)
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def render_pdf(report_text: str, out_path: str, title: str, subtitle: str):
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    base = styles["BodyText"]
    base.fontName = "Helvetica"
    base.fontSize = 10
    base.leading = 13

    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=18, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=14, spaceBefore=10, spaceAfter=6)

    # Stile link: blu + sottolineato
    link_style = ' color="blue"'
    # In Platypus: <a href="...">testo</a> è cliccabile; <u> sottolinea.

    story = []
    story.append(Paragraph(_escape(title), h1))
    story.append(Paragraph(_escape(subtitle), base))
    story.append(Spacer(1, 0.4*cm))

    # Regole: righe che iniziano con "SECTION" o emoji o "HEADLINE:" => heading
    for raw_line in report_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
            continue

        # Heading heuristics
        if line.startswith("HEADLINE:") or line.startswith("SECTION") or line.startswith("🔮") or line.startswith("🏢") or line.startswith("🌍") or line.startswith("🔬") or line.startswith("📊"):
            story.append(Paragraph(_escape(line), h2))
            continue

        # Trasforma "Source: <url>" in link bello "Source"
        # e anche righe che contengono un URL nudo
        url_match = re.search(r"(https?://\S+)", line)
        if url_match:
            url = url_match.group(1).rstrip(").,;")
            left = line[:url_match.start()].rstrip()
            right = line[url_match.end():].lstrip()

            # Se c'è "Source:" metti link pulito "Source"
            if "Source" in left:
                left_clean = left.replace("Source:", "").replace("Source", "").strip()
                html = f'{_escape(left_clean)} <a href="{_escape(url)}"><u><font{link_style}>Source</font></u></a> {_escape(right)}'
            else:
                # Se è un bullet con URL, rendi l'URL cliccabile ma mostra "Source"
                html = f'{_escape(left)} <a href="{_escape(url)}"><u><font{link_style}>{_escape(url)}</font></u></a> {_escape(right)}'

            story.append(Paragraph(html, base))
        else:
            story.append(Paragraph(_escape(line), base))

    doc.build(story)

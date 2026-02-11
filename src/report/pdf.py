from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from textwrap import wrap
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

def render_pdf(report_text: str, out_path: str, title: str, subtitle: str):
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4

    x = 2 * cm
    y = height - 2 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, title)
    y -= 0.8 * cm

    c.setFont("Helvetica", 10)
    c.drawString(x, y, subtitle)
    y -= 1.0 * cm

    c.setFont("Helvetica", 10)
    for paragraph in report_text.split("\n"):
        if not paragraph.strip():
            y -= 0.35 * cm
            continue

        for line in wrap(paragraph, 110):

            if y < 2 * cm:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 2 * cm

            # Detect source line
            if "Source:" in line:
                parts = line.split("Source:")
                text_part = parts[0]
                url = parts[1].strip()
                url_part = " Source"

                # Draw normal text first
                c.setFillColor(colors.black)
                c.drawString(x, y, text_part)

                # Calculate X offset for URL
                offset = stringWidth(text_part, "Helvetica", 10)

                # Draw URL in blue
                c.setFillColor(colors.blue)
                c.drawString(x + offset, y, url_part)

                # Underline URL
                url_width = stringWidth(url_part, "Helvetica", 10)
                c.line(x + offset, y - 1, x + offset + url_width, y - 1)

                # Optional: make it clickable
                c.linkURL(
                    parts[1].strip(),
                    (x + offset, y - 2, x + offset + url_width, y + 10),
                    relative=0
                )

                c.setFillColor(colors.black)

            else:
                c.drawString(x, y, line)

            y -= 0.45 * cm

    c.save()

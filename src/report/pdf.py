from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from textwrap import wrap

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
            c.drawString(x, y, line)
            y -= 0.45 * cm

    c.save()

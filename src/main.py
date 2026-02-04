import os
from datetime import datetime
from report.drive_upload import upload_to_drive
from reportlab.pdfgen import canvas

def create_dummy_pdf(path):
    c = canvas.Canvas(path)
    c.drawString(100, 750, "Weekly Automotive Brief")
    c.drawString(100, 730, f"Generated: {datetime.utcnow()}")
    c.save()

def run():
    filename = "weekly_brief.pdf"
    create_dummy_pdf(filename)

    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    link = upload_to_drive(filename, folder_id)

    print("Uploaded to Drive:")
    print(link)

if __name__ == "__main__":
    run()

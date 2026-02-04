import os
from datetime import datetime
from reportlab.pdfgen import canvas
from report.drive_upload import upload_pdf_to_drive

def make_test_pdf(path: str):
    c = canvas.Canvas(path)
    c.drawString(72, 760, "Auto Weekly Brief - Upload Test")
    c.drawString(72, 740, f"Generated at (UTC): {datetime.utcnow().isoformat()}Z")
    c.save()

def main():
    out = "weekly_brief_TEST.pdf"
    make_test_pdf(out)

    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    link = upload_pdf_to_drive(out, folder_id)

    print("✅ Uploaded to Google Drive")
    print(link)

if __name__ == "__main__":
    main()

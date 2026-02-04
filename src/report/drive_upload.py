# src/report/drive_upload.py
import os, json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_drive(local_path: str, folder_id: str):
    service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )

    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": os.path.basename(local_path),
        "parents": [folder_id],
    }

    media = MediaFileUpload(local_path, mimetype="application/pdf", resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink",
        supportsAllDrives=True,          # <<< important for Shared Drives
    ).execute()

    return file["webViewLink"]

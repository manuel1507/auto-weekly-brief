import os, json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def upload_to_drive(local_path: str, folder_id: str) -> str:
    """
    Uploads a file to Google Drive using Service Account credentials stored in env.
    Returns a webViewLink.
    """
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": os.path.basename(local_path),
        "parents": [folder_id],
    }

    media = MediaFileUpload(local_path, mimetype="application/pdf", resumable=True)

    created = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    return created["webViewLink"]
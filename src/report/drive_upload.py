import os, json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def upload_to_drive(local_path: str, folder_id: str) -> str:
    """
    Uploads a file to the user's Google Drive (consumer Gmail) using OAuth token stored in env.
    Refreshes token automatically if expired.
    Returns a webViewLink.
    """
    token_info = json.loads(os.environ["GOOGLE_OAUTH_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # Auto-refresh in GitHub Actions
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

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



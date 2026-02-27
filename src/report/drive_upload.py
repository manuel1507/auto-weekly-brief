import os
import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def upload_to_drive(local_path: str, folder_id: str) -> str:
    """
    Uploads a file to the user's Google Drive using OAuth token stored in env (Gmail personale).
    Refreshes token automatically if expired.
    Returns a webViewLink.
    """
    token_raw = os.environ.get("GOOGLE_OAUTH_TOKEN_JSON")
    if not token_raw:
        raise RuntimeError(
            "Missing env var GOOGLE_OAUTH_TOKEN_JSON. "
            "Set it in GitHub Secrets and pass it via the workflow env."
        )

    try:
        token_info = json.loads(token_raw)
    except json.JSONDecodeError as e:
        raise RuntimeError("GOOGLE_OAUTH_TOKEN_JSON is not valid JSON.") from e

    creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # Auto-refresh in GitHub Actions
    if creds.expired:
        if not creds.refresh_token:
            raise RuntimeError(
                "OAuth access token is expired and no refresh_token is present. "
                "Regenerate the token with access_type='offline' and prompt='consent'."
            )
        try:
            creds.refresh(Request())
        except Exception as e:
            # Common root cause: invalid_grant (refresh token expired/revoked)
            raise RuntimeError(
                "Failed to refresh OAuth token (often 'invalid_grant'). "
                "Re-generate GOOGLE_OAUTH_TOKEN_JSON after setting OAuth consent screen to 'In produzione'."
            ) from e

    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": os.path.basename(local_path),
        "parents": [folder_id],
    }

    media = MediaFileUpload(local_path, mimetype="application/pdf", resumable=True)

    try:
        created = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink"
        ).execute()
    except HttpError as e:
        # Give a clearer message for permission / folder issues
        raise RuntimeError(
            "Google Drive upload failed. Check that GOOGLE_DRIVE_FOLDER_ID is correct "
            "and that the OAuth user has access to that folder."
        ) from e

    # Keep behavior consistent: return webViewLink (KeyError if missing is unlikely but same as before)
    return created["webViewLink"]
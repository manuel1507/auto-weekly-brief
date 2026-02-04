import os, json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def main():
    client_json = os.environ["GOOGLE_OAUTH_CLIENT_JSON"]
    with open("client_secret.json", "w") as f:
        f.write(client_json)

    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    print("\n1) Open this URL in your browser:\n")
    print(auth_url)
    print("\n2) Approve access, then paste the authorization code here.\n")

    code = input("Authorization code: ").strip()

    flow.fetch_token(code=code)

    with open("token.json", "w") as f:
        f.write(flow.credentials.to_json())

    print("\n✅ token.json created\n")

if __name__ == "__main__":
    main()

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
REDIRECT_URI = "https://solid-umbrella-rpgv7jj7w7pc5rgv-8080.app.github.dev/"

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
flow.redirect_uri = REDIRECT_URI

auth_url, _ = flow.authorization_url(
    access_type="offline",
    include_granted_scopes="true",
    prompt="consent",
)

print(auth_url)
redirected_url = input("Paste full redirected URL: ").strip()
flow.fetch_token(authorization_response=redirected_url)

open("token.json", "w").write(flow.credentials.to_json())
print("OK token.json created")
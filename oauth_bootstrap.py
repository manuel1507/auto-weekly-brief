from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)

# IMPORTANT: console flow (works in Codespaces)
creds = flow.run_console()

with open("token.json", "w") as f:
    f.write(creds.to_json())

print("✅ token.json created (save it as a GitHub Secret GOOGLE_OAUTH_TOKEN_JSON)")
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

flow = InstalledAppFlow.from_client_secrets_file(
    str(Path.home() / "Dev/kraftdo_handoff/gmail_oauth_credentials.json"),
    SCOPES,
    redirect_uri="urn:ietf:wg:oauth:2.0:oob"
)
auth_url, _ = flow.authorization_url(prompt="consent")
print("\nAbre este link en el browser:")
print(f"\n{auth_url}\n")
code = input("Pega el código aquí: ").strip()
flow.fetch_token(code=code)

token_json = flow.credentials.to_json()
Path.home().joinpath("Dev/kraftdo_handoff/.gmail_token.json").write_text(token_json)
Path("~/Dev/kraftdo_meme/.sheets_token.json").expanduser().write_text(token_json)
print("✅ Token actualizado con scopes de Sheets y Gmail")

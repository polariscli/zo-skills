#!/usr/bin/env python3
"""step 1: print the authorization url."""
import json
import secrets

CREDS_FILE = "/home/.z/whoop/credentials.json"
STATE_FILE = "/home/.z/whoop/oauth_state.txt"
WHOOP_BASE_URL = "https://api.prod.whoop.com"
REDIRECT_URI = "http://localhost:8080/callback"

with open(CREDS_FILE) as f:
    creds = json.load(f)

CLIENT_ID = creds["client_id"]

# generate secure random state
state = secrets.token_urlsafe(32)

# save state for verification in step 2
with open(STATE_FILE, "w") as f:
    f.write(state)

auth_url = (
    f"{WHOOP_BASE_URL}/oauth/oauth2/auth?"
    f"client_id={CLIENT_ID}&"
    f"redirect_uri={REDIRECT_URI}&"
    f"response_type=code&"
    f"scope=offline read:sleep read:recovery&"
    f"state={state}"
)

print("\n=== whoop oauth - step 1 ===\n")
print("visit this url in your browser:\n")
print(auth_url)
print("\nafter authorizing, you'll be redirected to:")
print("http://localhost:8080/callback?code=XXXXX&state=XXXXX")
print("\ncopy the FULL url (including the code and state parameters)")
print("then run: python step2-exchange-code.py 'PASTE_URL_HERE'")

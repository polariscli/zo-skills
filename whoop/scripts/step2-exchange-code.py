#!/usr/bin/env python3
"""step 2: exchange authorization code for tokens."""
import json
import sys
import requests
from urllib.parse import urlparse, parse_qs

CREDS_FILE = "/home/.z/whoop/credentials.json"
STATE_FILE = "/home/.z/whoop/oauth_state.txt"
TOKENS_FILE = "/home/.z/whoop/tokens.json"
WHOOP_BASE_URL = "https://api.prod.whoop.com"
TOKEN_URL = f"{WHOOP_BASE_URL}/oauth/oauth2/token"
REDIRECT_URI = "http://localhost:8080/callback"

if len(sys.argv) < 2:
    print("usage: python step2-exchange-code.py 'http://localhost:8080/callback?code=XXXXX&state=XXXXX'")
    sys.exit(1)

redirect_url = sys.argv[1]

# extract code and state from url
parsed = urlparse(redirect_url)
params = parse_qs(parsed.query)

if "code" not in params:
    print("error: no code found in url")
    sys.exit(1)

if "state" not in params:
    print("error: no state found in url")
    sys.exit(1)

code = params["code"][0]
state = params["state"][0]

# verify state matches what we sent
with open(STATE_FILE) as f:
    expected_state = f.read().strip()

if state != expected_state:
    print("error: state mismatch - possible CSRF attack")
    sys.exit(1)

print(f"✓ state verified")
print(f"✓ extracted code: {code[:20]}...")

# load credentials
with open(CREDS_FILE) as f:
    creds = json.load(f)

# exchange code for tokens
print("\nexchanging code for tokens...")
response = requests.post(
    TOKEN_URL,
    data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
    },
)

if response.status_code != 200:
    print(f"error: {response.status_code}")
    print(response.text)
    sys.exit(1)

tokens = response.json()
print("✓ got tokens")

# save tokens
with open(TOKENS_FILE, "w") as f:
    json.dump(tokens, f, indent=2)

print(f"✓ saved to {TOKENS_FILE}")
print("\nauthentication complete! webhook system is now ready.")

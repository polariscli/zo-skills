#!/usr/bin/env python3
"""
manual whoop oauth - for remote environments
prints auth url, waits for you to paste the callback url
"""

import json
import requests
from pathlib import Path

CREDS_PATH = "/home/.z/whoop/credentials.json"
TOKEN_PATH = "/home/.z/whoop/tokens.json"
WHOOP_BASE_URL = "https://api.prod.whoop.com"
TOKEN_URL = f"{WHOOP_BASE_URL}/oauth/oauth2/token"
REDIRECT_URI = "http://localhost:8080/callback"

# load creds
with open(CREDS_PATH) as f:
    creds = json.load(f)

CLIENT_ID = creds['client_id']
CLIENT_SECRET = creds['client_secret']

# build auth url
auth_url = (
    f"{WHOOP_BASE_URL}/oauth/oauth2/auth?"
    f"client_id={CLIENT_ID}&"
    f"redirect_uri={REDIRECT_URI}&"
    f"response_type=code&"
    f"scope=offline read:sleep read:recovery"
)

print("\n=== whoop oauth setup ===\n")
print("1. visit this url in your browser:")
print(f"\n   {auth_url}\n")
print("2. authorize the app")
print("3. you'll be redirected to localhost:8080/callback?code=...")
print("4. paste the FULL redirect url here\n")

redirect_url = input("paste redirect url: ").strip()

# extract code
if "code=" not in redirect_url:
    print("error: no code found in url")
    exit(1)

code = redirect_url.split("code=")[1].split("&")[0]
print(f"\nextracted code: {code[:20]}...")

# exchange for tokens
print("exchanging code for tokens...")
response = requests.post(TOKEN_URL, data={
    'grant_type': 'authorization_code',
    'code': code,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI
})

if response.status_code != 200:
    print(f"error: {response.text}")
    exit(1)

tokens = response.json()
from datetime import datetime
tokens['expires_at'] = datetime.now().timestamp() + tokens['expires_in']

# save tokens
TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(TOKEN_PATH, 'w') as f:
    json.dump(tokens, f, indent=2)

print(f"\n✓ authenticated successfully!")
print(f"✓ tokens saved to {TOKEN_PATH}")
print(f"\ntest with: python whoop.py status")

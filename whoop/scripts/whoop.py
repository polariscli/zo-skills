#!/usr/bin/env python3
"""
whoop cli - sleep tracking and status monitoring
"""

import argparse
import json
import os
import requests
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

WHOOP_BASE_URL = "https://api.prod.whoop.com"
AUTH_URL = f"{WHOOP_BASE_URL}/oauth/oauth2/auth"
TOKEN_URL = f"{WHOOP_BASE_URL}/oauth/oauth2/token"
REDIRECT_URI = "https://polaris.zo.computer/oauth-callback"

TOKEN_PATH = Path("/home/.z/whoop/tokens.json")
CREDS_PATH = Path("/home/.z/whoop/credentials.json")

def load_credentials():
    """load client credentials from file."""
    with open(CREDS_PATH) as f:
        return json.load(f)

CREDS = load_credentials()
CLIENT_ID = CREDS["client_id"]
CLIENT_SECRET = CREDS["client_secret"]

# oauth callback handler
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    
    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>')
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # suppress logs

def ensure_token_dir():
    """ensure token directory exists."""
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_tokens():
    """load tokens from file."""
    if not TOKEN_PATH.exists():
        return None
    with open(TOKEN_PATH) as f:
        return json.load(f)

def save_tokens(tokens):
    """save tokens to file."""
    ensure_token_dir()
    with open(TOKEN_PATH, 'w') as f:
        json.dump(tokens, f, indent=2)
    print(f"✓ tokens saved to {TOKEN_PATH}")

def refresh_token_if_needed():
    """refresh access token if expired."""
    tokens = load_tokens()
    if not tokens:
        print("no tokens found. run: python whoop.py auth")
        return None
    
    # check expiration
    expires_at = tokens.get('expires_at', 0)
    if datetime.now().timestamp() < expires_at - 300:  # 5 min buffer
        return tokens['access_token']
    
    # refresh
    response = requests.post(TOKEN_URL, data={
        'grant_type': 'refresh_token',
        'refresh_token': tokens['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'offline read:sleep read:recovery'
    })
    
    if response.status_code != 200:
        print(f"failed to refresh token: {response.text}")
        return None
    
    new_tokens = response.json()
    tokens.update({
        'access_token': new_tokens['access_token'],
        'refresh_token': new_tokens.get('refresh_token', tokens['refresh_token']),
        'expires_at': datetime.now().timestamp() + new_tokens['expires_in']
    })
    
    save_tokens(tokens)
    return tokens['access_token']

def make_api_request(endpoint, params=None):
    """make authenticated api request."""
    access_token = refresh_token_if_needed()
    if not access_token:
        return None
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{WHOOP_BASE_URL}{endpoint}", headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"api error: {response.status_code} - {response.text}")
        return None
    
    return response.json()

def cmd_auth(args):
    """authenticate with whoop via oauth."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("error: WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET must be set in environment")
        print("add them to Settings > Developers > Secrets")
        return
    
    # start local server for callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    
    # build auth url
    auth_url = (
        f"{AUTH_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=offline read:sleep read:recovery"
    )
    
    print("opening browser for authorization...")
    webbrowser.open(auth_url)
    
    print("waiting for callback...")
    server.handle_request()
    
    if not OAuthCallbackHandler.auth_code:
        print("authorization failed - no code received")
        return
    
    # exchange code for tokens
    response = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': OAuthCallbackHandler.auth_code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI
    })
    
    if response.status_code != 200:
        print(f"token exchange failed: {response.text}")
        return
    
    tokens = response.json()
    tokens['expires_at'] = datetime.now().timestamp() + tokens['expires_in']
    save_tokens(tokens)
    
    print("✓ authentication successful")

def cmd_status(args):
    """check authentication status."""
    tokens = load_tokens()
    if not tokens:
        print("not authenticated. run: python whoop.py auth")
        return
    
    expires_at = datetime.fromtimestamp(tokens.get('expires_at', 0))
    if datetime.now() > expires_at:
        print("⚠ token expired - will refresh on next api call")
    else:
        time_left = expires_at - datetime.now()
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        print(f"✓ authenticated - token expires in {hours}h {minutes}m")

def cmd_sleep(args):
    """get recent sleep data."""
    end = datetime.now()
    start = end - timedelta(days=args.days)
    
    params = {
        'start': start.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'end': end.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    }
    
    data = make_api_request('/developer/v2/activity/sleep', params)
    if not data:
        return
    
    records = data.get('records', [])
    if not records:
        print(f"no sleep data found for last {args.days} days")
        return
    
    print(f"🛌 sleep data (last {args.days} days):\n")
    for sleep in records:
        start_time = datetime.fromisoformat(sleep['start'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(sleep['end'].replace('Z', '+00:00'))
        duration = (end_time - start_time).total_seconds() / 3600
        
        score = sleep.get('score', {})
        sleep_efficiency = score.get('sleep_efficiency_percentage', 0)
        
        print(f"  {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}")
        print(f"    duration: {duration:.1f}h")
        print(f"    efficiency: {sleep_efficiency}%")
        print(f"    id: {sleep['id']}")
        print()

def cmd_is_sleeping(args):
    """check if currently sleeping."""
    # get sleep from last 24 hours
    end = datetime.now()
    start = end - timedelta(hours=24)
    
    params = {
        'start': start.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'end': end.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    }
    
    data = make_api_request('/developer/v2/activity/sleep', params)
    if not data:
        return
    
    records = data.get('records', [])
    if not records:
        print("no recent sleep data")
        return
    
    # check most recent sleep
    latest = records[-1]
    start_time = datetime.fromisoformat(latest['start'].replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(latest['end'].replace('Z', '+00:00'))
    now = datetime.now(start_time.tzinfo)
    
    if start_time <= now <= end_time:
        duration_hours = (now - start_time).total_seconds() / 3600
        print(f"✓ sleeping (started {duration_hours:.1f}h ago)")
        print(f"  sleep_id: {latest['id']}")
        return True
    else:
        hours_since = (now - end_time).total_seconds() / 3600
        print(f"awake (last sleep ended {hours_since:.1f}h ago)")
        return False

def cmd_sleep_details(args):
    """get detailed sleep stage breakdown."""
    data = make_api_request(f'/v2/activity/sleep/{args.sleep_id}')
    if not data:
        return
    
    start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    duration = (end_time - start_time).total_seconds() / 3600
    
    score = data.get('score', {})
    
    print(f"🛌 sleep details:\n")
    print(f"  date: {start_time.strftime('%Y-%m-%d')}")
    print(f"  time: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
    print(f"  duration: {duration:.1f}h")
    print(f"  efficiency: {score.get('sleep_efficiency_percentage', 0)}%")
    print()
    
    if 'stage_summary' in score:
        stages = score['stage_summary']
        print("  stage breakdown:")
        for stage_name, stage_data in stages.items():
            minutes = stage_data.get('total_in_bed_time_milli', 0) / 60000
            print(f"    {stage_name}: {minutes:.0f}min")

def main():
    parser = argparse.ArgumentParser(description="whoop cli - sleep tracking")
    subparsers = parser.add_subparsers(dest="command", help="command")
    
    # auth command
    auth_parser = subparsers.add_parser("auth", help="authenticate with whoop")
    auth_parser.set_defaults(func=cmd_auth)
    
    # status command
    status_parser = subparsers.add_parser("status", help="check auth status")
    status_parser.set_defaults(func=cmd_status)
    
    # sleep command
    sleep_parser = subparsers.add_parser("sleep", help="get recent sleep data")
    sleep_parser.add_argument("--days", type=int, default=7, help="days of history (default: 7)")
    sleep_parser.set_defaults(func=cmd_sleep)
    
    # is-sleeping command
    is_sleeping_parser = subparsers.add_parser("is-sleeping", help="check if currently sleeping")
    is_sleeping_parser.set_defaults(func=cmd_is_sleeping)
    
    # sleep-details command
    details_parser = subparsers.add_parser("sleep-details", help="get sleep stage details")
    details_parser.add_argument("sleep_id", help="sleep id (uuid)")
    details_parser.set_defaults(func=cmd_sleep_details)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)

if __name__ == "__main__":
    main()

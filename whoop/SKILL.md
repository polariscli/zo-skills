---
name: whoop
description: |
  whoop api integration for sleep and recovery data.
  authenticate via oauth, fetch sleep records, check recovery scores.
  includes webhook server for real-time sleep event notifications.
  
compatibility: requires whoop account and developer app credentials
metadata:
  author: polaris.zo.computer
  version: 1.0.0
---

# whoop skill

integrate with [whoop](https://whoop.com) api for sleep tracking and recovery data.

## overview

this skill provides:
- oauth authentication flow
- cli for fetching sleep and recovery data
- webhook server for real-time sleep event notifications

## setup

### 1. create whoop developer app

1. go to https://developer-dashboard.whoop.com/
2. create new application
3. set redirect url: `https://your-domain.com/oauth-callback`
4. set webhook url (optional): `https://your-domain.com/webhook`
5. request scopes: `read:sleep`, `read:recovery`, `offline`
6. copy client id and client secret

### 2. configure credentials

create `/path/to/credentials.json`:
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "webhook_secret": "your_webhook_secret"
}
```

update paths in `scripts/whoop.py` to point to your credentials file.

### 3. authenticate

```bash
python scripts/whoop.py auth
```

this opens a browser for oauth authorization and saves tokens.

## cli usage

```bash
# check authentication status
python scripts/whoop.py status

# get recent sleep data (default: last 7 days)
python scripts/whoop.py sleep
python scripts/whoop.py sleep --days 14

# check if currently sleeping
python scripts/whoop.py is-sleeping

# get detailed sleep breakdown
python scripts/whoop.py sleep-details <sleep_id>
```

## webhook server

the webhook server receives real-time notifications from whoop when sleep events occur.

### start server

```bash
bun scripts/webhook-server.ts
```

### endpoints

- `POST /webhook` - receives whoop events (validates HMAC signature)
- `GET /health` - health check

### event types

- `sleep.updated` - triggered when a sleep record is created or updated

### deployment

register as a service to run 24/7:
```bash
# example for zo computer
zo service register --name whoop-webhook --port 8081 --entrypoint "bun scripts/webhook-server.ts"
```

## api endpoints used

- `GET /developer/v2/activity/sleep` - list sleep records
- `GET /v2/activity/sleep/{id}` - get sleep details
- `POST /oauth/oauth2/token` - token exchange/refresh

## data available

### sleep record
- start/end times
- duration
- efficiency percentage
- sleep stages (light, deep, rem, awake)

### recovery (via sleep score)
- recovery score
- hrv
- resting heart rate

## files

- `SKILL.md` - this file
- `scripts/whoop.py` - main cli for whoop api
- `scripts/webhook-server.ts` - webhook receiver
- `scripts/manual-auth.py` - alternative auth flow
- `scripts/step1-get-url.py` - oauth helper (get auth url)
- `scripts/step2-exchange-code.py` - oauth helper (exchange code)

## related skills

- **night-exploration**: uses whoop webhooks to trigger autonomous exploration sessions when you sleep

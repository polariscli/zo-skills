#!/bin/bash
# whoop webhook watchdog
# monitors webhook server and restarts if dead

SERVER_SCRIPT="/home/workspace/Skills/whoop/scripts/webhook-server.ts"
LOG_FILE="/dev/shm/whoop-webhook.log"
PID_FILE="/dev/shm/whoop-webhook.pid"
CHECK_INTERVAL=10

start_server() {
  echo "[$(date)] starting whoop webhook server..."
  cd /home/workspace/Skills/whoop
  nohup bun "$SERVER_SCRIPT" >> "$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"
  echo "[$(date)] server started (pid: $pid)"
}

monitor_server() {
  while true; do
    sleep "$CHECK_INTERVAL"

    if [ ! -f "$PID_FILE" ]; then
      echo "[$(date)] pid file missing, starting server..."
      start_server
      continue
    fi

    local pid=$(cat "$PID_FILE")
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "[$(date)] server died (pid: $pid), restarting..."
      start_server
      continue
    fi

    # health check
    if ! timeout 5 curl -s http://localhost:8081/health >/dev/null 2>&1; then
      echo "[$(date)] health check failed, killing and restarting..."
      kill -9 "$pid" 2>/dev/null
      start_server
      continue
    fi
  done
}

# cleanup on exit
trap "rm -f '$PID_FILE'" EXIT

echo "[$(date)] whoop webhook watchdog started"
start_server
monitor_server

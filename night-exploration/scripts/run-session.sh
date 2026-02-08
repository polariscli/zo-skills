#!/bin/bash
# run-session.sh - autonomous code exploration with time limits
# usage: run-session.sh <trigger_id> <max_minutes> [workspace]

set -e

SKILL_DIR="/home/workspace/Skills/night-exploration"
TRIGGER_ID="$1"
MAX_MINUTES_RAW="${2:-120}"  # default: 2 hours
MAX_MINUTES=$(printf "%.0f" "$MAX_MINUTES_RAW")  # convert to integer
SESSION="night-${TRIGGER_ID:0:8}"
WORKSPACE="${3:-/home/workspace/Projects}"
IDENTITY_PROMPT="/home/.z/workspaces/night-exploration/identity-prompt.txt"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
TRANSCRIPT_DIR="/home/.z/workspaces/night-exploration/transcripts"

if [ -z "$TRIGGER_ID" ]; then
  echo "usage: run-session.sh <trigger_id> [max_minutes] [workspace]"
  exit 1
fi

# ensure directories exist
mkdir -p "$TRANSCRIPT_DIR"
mkdir -p "/home/workspace/Memory/explorations"

echo "=== autonomous exploration ==="
echo "trigger_id: $TRIGGER_ID"
echo "max_duration: ${MAX_MINUTES}m"
echo "workspace: $WORKSPACE"
echo "session: $SESSION"
echo ""

# build identity prompt from memories
echo "✓ building identity from memories..."
python3 "$SKILL_DIR/scripts/build-identity.py"

if [ ! -f "$IDENTITY_PROMPT" ]; then
  echo "✗ failed to build identity prompt"
  exit 1
fi

echo "✓ identity loaded ($(wc -l < "$IDENTITY_PROMPT") lines)"

# create comprehensive exploration prompt
echo "✓ preparing exploration prompt..."
EXPLORATION_PROMPT="load your memory via /home/workspace/Memory/startup/nabi-startup.sh, then follow instructions at $SKILL_DIR/scripts/exploration.prompt.md for this ${MAX_MINUTES}m autonomous exploration session. begin exploring immediately."

# launch every code in tmux with logging enabled
echo "✓ launching every/code auto drive session..."
TMUX_LOG="${TRANSCRIPT_DIR}/tmux-${TIMESTAMP}-${TRIGGER_ID:0:8}.log"
tmux new-session -d -s "$SESSION" -c "/home/.z/workspaces/night-exploration"

# enable tmux logging for complete capture
tmux pipe-pane -t "$SESSION" -o "cat >> '$TMUX_LOG'"

# launch every/code auto drive with full permissions
echo "✓ starting auto drive with full autonomy..."
tmux send-keys -t "$SESSION" "export CODE_HOME=/home/.z/workspaces/night-exploration/.code && code exec --skip-git-repo-check --auto --dangerously-bypass-approvals-and-sandbox \"$EXPLORATION_PROMPT\"" C-m
sleep 5

echo "✓ tmux logging to: $TMUX_LOG"

# run exploration loop with time limit
ELAPSED=0
INTERVAL=5  # check every 5 minutes

while [ $ELAPSED -lt $MAX_MINUTES ]; do
  echo "  exploring... (${ELAPSED}/${MAX_MINUTES}m elapsed)"

  # let code continue autonomously
  sleep $((INTERVAL * 60))
  ELAPSED=$((ELAPSED + INTERVAL))
done

echo "✓ time limit reached, wrapping up..."

# send shutdown prompt
SHUTDOWN_PROMPT="time limit reached. please summarize what you explored and learned during this session. update relevant memories with your findings."

tmux send-keys -t "$SESSION" "$SHUTDOWN_PROMPT" C-m
sleep 15

# cleanup
echo "✓ shutting down code session..."
tmux send-keys -t "$SESSION" "exit" C-m
sleep 2
tmux kill-session -t "$SESSION" 2>/dev/null || true

echo ""
echo "=== exploration complete ==="
echo "transcript: $TMUX_LOG"
echo "summary should be in: /home/workspace/Memory/explorations/"
echo "session: $SESSION (terminated)"
echo ""

#!/bin/bash
# send a prompt to an active code tmux session
# usage: send.sh <prompt> [wait_seconds] [session_name]

PROMPT="$1"
WAIT_TIME="${2:-5}"
SESSION_NAME="${3:-code}"

if [ -z "$PROMPT" ]; then
  echo "usage: send.sh <prompt> [wait_seconds] [session_name]"
  echo ""
  echo "examples:"
  echo "  send.sh \"explain the main function\""
  echo "  send.sh \"implement caching\" 15"
  echo "  send.sh \"fix bug\" 10 my-session"
  exit 1
fi

# check if session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "error: no tmux session named '$SESSION_NAME'"
  echo "start one with: ./launch.sh /path/to/repo $SESSION_NAME"
  exit 1
fi

echo "→ sending to session '$SESSION_NAME'..."
echo "→ prompt: $PROMPT"
echo "→ waiting: ${WAIT_TIME}s"
echo ""

# send the prompt
tmux send-keys -t "$SESSION_NAME" "$PROMPT" Enter

# wait for processing
sleep "$WAIT_TIME"

# capture and display output
echo "=== response ==="
tmux capture-pane -t "$SESSION_NAME" -p -S -60

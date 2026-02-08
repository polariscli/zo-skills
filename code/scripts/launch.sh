#!/bin/bash
# launch code in a tmux session
# usage: launch.sh [repo_path] [session_name]

REPO_PATH="${1:-.}"
SESSION_NAME="${2:-code}"

if [ ! -d "$REPO_PATH" ]; then
  echo "error: $REPO_PATH is not a directory"
  exit 1
fi

# resolve to absolute path
REPO_PATH="$(cd "$REPO_PATH" && pwd)"

# kill existing session if it exists
tmux kill-session -t "$SESSION_NAME" 2>/dev/null

# create new session with proper size
tmux new-session -d -s "$SESSION_NAME" -x 200 -y 50 -c "$REPO_PATH"

# launch code with script for proper tty handling
tmux send-keys -t "$SESSION_NAME" "script -q -c 'code' /dev/null" Enter

sleep 2

# show initial output
tmux capture-pane -t "$SESSION_NAME" -p

echo ""
echo "✓ code launched in tmux session '$SESSION_NAME'"
echo "  repo: $REPO_PATH"
echo ""
echo "commands:"
echo "  send prompt: ./send.sh \"your prompt\" [wait_seconds] [$SESSION_NAME]"
echo "  read output: ./capture.sh [$SESSION_NAME]"
echo "  attach:      tmux attach -t $SESSION_NAME"
echo "  kill:        tmux kill-session -t $SESSION_NAME"

#!/bin/bash
# capture output from a code tmux session
# usage: capture.sh [session_name] [lines]

SESSION_NAME="${1:-code}"
LINES="${2:-100}"

# check if session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "error: no tmux session named '$SESSION_NAME'"
  echo "start one with: ./launch.sh /path/to/repo $SESSION_NAME"
  exit 1
fi

# capture pane content
tmux capture-pane -t "$SESSION_NAME" -p -S -"$LINES"

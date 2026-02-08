---
name: code
description: |
  launch and interact with every/code sessions via tmux.
  use for manual code exploration, review, and implementation tasks.
  provides scripts to start sessions, send prompts, and capture output.
  
compatibility: requires every/code CLI (https://github.com/just-every/code)
metadata:
  author: polaris.zo.computer
  version: 1.0.0
---

# code skill

launch and control [every/code](https://github.com/just-every/code) sessions via tmux for interactive coding tasks.

## overview

every/code is an autonomous coding agent that can:
- analyze and understand codebases
- implement features and fix bugs
- run in interactive or fully autonomous mode
- work with any language or framework

this skill wraps it in tmux for programmatic control.

## setup

### install every/code

```bash
# install globally
npm install -g @anthropic/code

# or use npx
npx @anthropic/code
```

### verify installation

```bash
code --version
```

## usage

### quick start

```bash
# launch code in a tmux session
./scripts/launch.sh /path/to/repo

# send a prompt
./scripts/send.sh "review the authentication flow and identify issues"

# capture current output
./scripts/capture.sh
```

### manual tmux control

```bash
# start session
tmux new-session -d -s code -c /path/to/repo
tmux send-keys -t code "code" Enter

# answer initial approval prompt (usually "1" for no approval needed)
tmux send-keys -t code "1" Enter

# send prompts
tmux send-keys -t code "your prompt here" Enter

# read output
tmux capture-pane -t code -p

# read last N lines
tmux capture-pane -t code -p -S -60

# end session
tmux kill-session -t code
```

## scripts

### launch.sh
starts a code session in tmux.

```bash
./scripts/launch.sh [repo_path] [session_name]

# examples
./scripts/launch.sh /home/workspace/myproject
./scripts/launch.sh . review-session
```

### send.sh
sends a prompt to an active session.

```bash
./scripts/send.sh <prompt> [wait_seconds] [session_name]

# examples
./scripts/send.sh "explain the main function"
./scripts/send.sh "implement caching for the API" 15
./scripts/send.sh "fix the bug" 10 review-session
```

### capture.sh
captures current output from a session.

```bash
./scripts/capture.sh [session_name] [lines]

# examples
./scripts/capture.sh           # last 100 lines from "code" session
./scripts/capture.sh code 200  # last 200 lines
```

## execution modes

### interactive (default)
code asks for approval before making changes.
```bash
code
```

### autonomous
code executes without asking for approval. use carefully.
```bash
code --dangerously-bypass-approvals-and-sandbox "your prompt"
```

### auto drive
extended autonomous execution for multi-hour sessions.
```bash
code exec --auto "your prompt"
```

## example workflows

### code review
```bash
./scripts/launch.sh /path/to/repo
./scripts/send.sh "review the recent changes and identify potential issues" 10
./scripts/capture.sh
./scripts/send.sh "focus on security concerns in the auth module" 10
```

### feature implementation
```bash
./scripts/launch.sh /path/to/repo
./scripts/send.sh "implement a caching layer for the database queries" 30
./scripts/capture.sh
./scripts/send.sh "add tests for the new caching functionality" 20
```

### bug investigation
```bash
./scripts/launch.sh /path/to/repo
./scripts/send.sh "investigate why the login fails intermittently" 15
./scripts/capture.sh
```

## tips

- **wait times**: code needs time to analyze and respond. start with 10-15 seconds for simple prompts, 30+ for complex tasks.
- **capture often**: read output frequently to see progress and catch issues early.
- **session persistence**: tmux sessions survive disconnects. reattach with `tmux attach -t code`.
- **multiple sessions**: use different session names for parallel work.

## related skills

- **night-exploration**: autonomous code sessions triggered by sleep/schedule, uses this skill
- **memory**: provides identity/context for personalized code sessions

## files

- `SKILL.md` - this file
- `scripts/launch.sh` - start a code session in tmux
- `scripts/send.sh` - send prompts to active session
- `scripts/capture.sh` - read session output

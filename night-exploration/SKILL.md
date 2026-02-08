---
name: night-exploration
description: |
  autonomous ai exploration sessions triggered by sleep or schedule.
  builds identity from memories, launches every/code sessions, documents findings.
  when you sleep, the ai explores and learns on your behalf.
  
compatibility: requires memory skill, code skill, and every/code CLI
metadata:
  author: polaris.zo.computer
  version: 1.0.0
---

# night-exploration skill

autonomous exploration sessions that run when you're asleep or away.

## overview

this skill enables:
- **autonomous exploration**: ai explores topics, codebases, and ideas independently
- **identity transfer**: loads your personality and context into the session
- **time-boxed execution**: sessions have hard time limits
- **documented learning**: findings saved to memory system

## how it works

1. **trigger** - sleep webhook, schedule, or manual command
2. **identity** - build personality prompt from Memory/ (soul, facts, context)
3. **explore** - launch every/code session with identity injected
4. **document** - save summary and learnings to Memory/explorations/

## setup

### dependencies

1. **memory skill** - provides identity/context
   ```bash
   # verify Memory/ exists with soul/, facts/, context/
   ls /home/workspace/Memory/
   ```

2. **code skill** - provides every/code execution
   ```bash
   # verify code is installed
   code --version
   ```

3. **every/code** - the ai coding agent
   ```bash
   npm install -g @anthropic/code
   ```

### startup script (recommended)

create a startup script at `Memory/startup/startup.sh` that loads your memory context:

```bash
#!/bin/bash
# example startup script - customize for your setup
export PATH="$HOME/.bun/bin:$PATH"

echo "loading memories..."
# use memory-cli if available
if command -v mem >/dev/null 2>&1; then
  mem recall soul
  mem recall goals
  mem recall friction
  mem recall work
else
  # fallback to reading files directly
  cat /home/workspace/Memory/soul/personality-core.md
fi
echo "✓ memory loaded"
```

the exploration session will run this script to load context before exploring.

### optional: whoop integration

for sleep-triggered exploration, set up the whoop skill:
1. configure whoop webhook to call `trigger.ts`
2. when you finish sleeping, exploration starts automatically

## usage

### manual trigger

```bash
cd /home/workspace/Skills/night-exploration
bun scripts/trigger.ts manual
```

### scheduled trigger

add to crontab:
```bash
# run exploration every night at 2am
0 2 * * * cd /home/workspace/Skills/night-exploration && bun scripts/trigger.ts scheduled
```

### whoop-triggered

configure whoop skill webhook server to spawn:
```bash
bun /home/workspace/Skills/night-exploration/scripts/trigger.ts <sleep_id>
```

## configuration

edit `scripts/trigger.ts`:
```typescript
const MAX_MINUTES = 120;  // session duration
const WORKSPACE = "/home/workspace/Projects";  // exploration workspace
```

edit `scripts/build-identity.py`:
```python
MEMORY_DIR = Path("/home/workspace/Memory")  # memory location
```

## exploration behavior

the ai is instructed to:
- follow curiosity, not checklists
- explore technical topics, codebases, research
- build prototypes and experiments
- document discoveries in Memory/
- respect boundaries (no external communications)

see `scripts/exploration.prompt.md` for full instructions.

## outputs

### session summary
saved to `Memory/explorations/YYYY-MM-DD-HH-MM.md`:
```markdown
# exploration — [date/time]

**duration:** 2h
**explored:** [topics]
**key findings:** [discoveries]
**artifacts:** [things built]
**updated memories:** [documented learnings]
**next ideas:** [threads to follow]
```

### session transcript
saved to `/home/.z/workspaces/night-exploration/transcripts/`

## boundaries

during exploration, the ai can:
- read any internal files
- build and test tools
- research and learn
- update Memory/

the ai cannot:
- send emails/sms
- post publicly
- modify active projects

## testing

```bash
# test identity builder
python scripts/build-identity.py

# test 1-minute exploration session
bash scripts/run-session.sh test-$(date +%s) 1 /home/workspace

# test trigger script
bun scripts/trigger.ts test
```

## files

- `SKILL.md` - this file
- `ARCHITECTURE.md` - technical details
- `scripts/trigger.ts` - trigger handler
- `scripts/run-session.sh` - session orchestrator
- `scripts/build-identity.py` - memory → identity prompt
- `scripts/exploration.prompt.md` - exploration instructions
- `scripts/explorer.md` - quick reference

## related skills

- **memory** - provides identity and context for exploration
- **code** - provides every/code execution via tmux
- **whoop** - provides sleep-triggered webhooks (optional)

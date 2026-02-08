# night exploration architecture

## overview

autonomous ai exploration sessions triggered by external signals (sleep detection, schedule, manual).
uses every/code for execution and the memory skill for identity/context.

## components

### 1. trigger script
- **file**: `scripts/trigger.ts`
- **function**: validates trigger signal, launches exploration session
- **execution**: spawned by external trigger (webhook, cron, manual)

### 2. session runner
- **file**: `scripts/run-session.sh`
- **function**: orchestrates entire exploration session
- **duration**: configurable (default: 120 minutes)
- **steps**:
  1. build identity prompt from memories
  2. launch every/code in tmux session
  3. inject identity and exploration context
  4. monitor for duration limit
  5. capture outputs
  6. gracefully shutdown and save summary

### 3. identity builder
- **file**: `scripts/build-identity.py`
- **function**: assembles personality and context from Memory/ into single prompt
- **output**: identity prompt file for code session

### 4. exploration prompts
- **files**: `scripts/exploration.prompt.md`, `scripts/explorer.md`
- **function**: instructions for autonomous exploration behavior

## data flow

```
trigger signal (sleep webhook, cron, manual)
  → trigger.ts validates
    → spawn run-session.sh (detached)
      → build-identity.py
        → load Memory/soul/
        → load Memory/facts/
        → load Memory/context/
        → generate identity prompt
      → launch tmux + code
        → inject identity
        → explore autonomously
        → capture outputs
        → shutdown gracefully
      → save summary.md
```

## memory integration

identity is built from Memory/ directory (requires memory skill):

```
Memory/
├── soul/       → core personality, values, style
├── facts/      → user profile, preferences
├── context/    → current projects, recent work
├── patterns/   → learned behaviors
└── reflections/→ meta-learnings
```

**identity prompt structure:**
```
=== WHO YOU ARE ===
[soul memories]

=== KEY FACTS ===
[user profile, preferences]

=== CURRENT CONTEXT ===
[active projects]

=== EXPLORATION MODE ===
[exploration instructions]

=== SESSION INFO ===
[timestamp, duration, workspace]
```

## trigger sources

### whoop webhook (sleep-triggered)
when whoop detects sleep end, it sends a webhook that triggers exploration.
requires whoop skill configured with webhook server.

```
whoop cloud → webhook-server.ts (whoop skill) → trigger.ts
```

### scheduled (cron)
run exploration on a schedule:
```bash
# example: every night at 2am
0 2 * * * /path/to/trigger.ts manual
```

### manual
trigger directly:
```bash
bun scripts/trigger.ts manual
```

## configuration

**default settings:**
```bash
MAX_MINUTES=120          # 2 hours per session
WORKSPACE=/home/workspace/Projects
MEMORY_DIR=/home/workspace/Memory
OUTPUT_DIR=/home/workspace/Memory/explorations
```

**customization:**
- edit `trigger.ts` for MAX_MINUTES, WORKSPACE
- edit `build-identity.py` for which memories to load
- edit `exploration.prompt.md` for exploration behavior

## file locations

```
Skills/night-exploration/
├── SKILL.md
├── ARCHITECTURE.md
└── scripts/
    ├── trigger.ts           # trigger handler
    ├── run-session.sh       # session orchestrator
    ├── build-identity.py    # memory → identity
    ├── exploration.prompt.md # detailed exploration instructions
    └── explorer.md          # short exploration reference

# runtime outputs
/home/.z/workspaces/night-exploration/
├── transcripts/            # full session logs
└── identity-prompt.txt     # generated identity (ephemeral)

Memory/explorations/
└── YYYY-MM-DD-HH-MM.md     # session summaries
```

## security

- **time limits**: sessions hard-capped at configured duration
- **scoped access**: can read/write internal files, cannot send external communications
- **boundaries**: cannot modify active projects (only exploration/experiment areas)
- **transparency**: all exploration logged, summaries saved

## dependencies

- **memory skill**: provides identity/context for personalized sessions
- **code skill**: provides every/code execution via tmux
- **whoop skill** (optional): provides sleep-triggered webhooks

## testing

```bash
# test identity builder
python scripts/build-identity.py

# test exploration runner (1 minute)
bash scripts/run-session.sh test-$(date +%s) 1 /home/workspace

# manual trigger
bun scripts/trigger.ts manual
```

## design philosophy

**event-driven**: dormant until triggered, no polling or cron required.

**identity continuity**: code sessions are personalized with memories, not generic.

**time-boxed safety**: hard limits prevent runaway sessions.

**transparent autonomy**: everything logged, summaries on completion.

**memory feedback**: findings feed back into Memory/ for continuous learning.

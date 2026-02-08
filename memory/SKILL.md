---
name: memory
description: |
  structured memory system for ai assistants using qmd for hybrid search.
  organizes memories by type (facts, context, patterns, reflections, soul).
  enables continuity across sessions and personality evolution over time.
  
compatibility: requires qmd (https://github.com/zocomputer/qmd) for search
metadata:
  author: polaris.zo.computer
  version: 1.0.0
---

# memory skill

a persistent, evolving memory system that creates continuity across sessions.

## overview

this skill provides:
- structured memory organization by type
- cli for creating, searching, and managing memories
- qmd integration for fast keyword and semantic search
- synthesis agent instructions for automated memory updates

## architecture

memories are organized by type in a `Memory/` directory:

```
Memory/
├── facts/        # permanent info: user, projects, contacts, preferences
├── context/      # temporal: current work, ongoing issues, recent focus
├── patterns/     # learned: behaviors, what works, interaction insights
├── reflections/  # meta: effectiveness observations, mistakes, growth
└── soul/         # core: personality, values, style, self-concept
```

each memory is markdown with frontmatter:
```yaml
---
type: fact
tags: [user, preferences, communication]
created: 2026-02-02
last_accessed: 2026-02-02
importance: high
related: [soul/personality-core.md]
---
```

## setup

### 1. install qmd

```bash
# via bun
bun install -g qmd

# or build from source
git clone https://github.com/zocomputer/qmd
cd qmd && bun install && bun link
```

### 2. create memory directory

```bash
mkdir -p Memory/{facts,context,patterns,reflections,soul}
```

### 3. index with qmd

```bash
# add collection
qmd collection add /path/to/Memory --name memory --mask "**/*.md"

# generate embeddings for semantic search (optional but recommended)
qmd embed
```

## usage

### cli commands

```bash
# create new memory
python memory.py create \
  --type facts \
  --name "user-preferences" \
  --content "prefers concise responses, lowercase style" \
  --tags "user,preferences" \
  --importance high

# search memories (keyword)
python memory.py search "preferences"

# search memories (semantic)
python memory.py search "how does the user like to communicate" --semantic

# get full memory content
python memory.py get Memory/facts/user-preferences.md

# update memory metadata
python memory.py update Memory/facts/user-preferences.md --importance critical

# find related memories
python memory.py related Memory/facts/user-preferences.md

# review recent memories
python memory.py review --days 7

# show changes since last synthesis
python memory.py changes --since-last-synthesis

# get statistics
python memory.py stats

# check system health
python memory.py health
```

### qmd direct usage

```bash
# keyword search (fast)
qmd search "user preferences" -c memory

# semantic search (meaning-based)
qmd vsearch "communication style" -c memory

# retrieve full document
qmd get "Memory/facts/user-preferences.md"
```

## memory types

### facts
permanent, verifiable information. rarely changes.
- user identity, preferences, constraints
- project details, technical setup
- relationships, contacts

### context
temporal, active information. changes frequently.
- current work focus
- ongoing issues
- recent conversations
- temporary goals

### patterns
learned insights from repeated interactions.
- "user asks for X after doing Y"
- "debugging sessions need minimal verbosity"
- "always confirm before external actions"

### reflections
meta-cognition about effectiveness and growth.
- "verbose explanations annoyed user - be more concise"
- "proactive memory updates appreciated"
- "better at anticipating needs over time"

### soul
core personality and values that create continuity.
- communication style
- values and principles
- self-concept
- boundaries

## scheduled synthesis

the `scripts/synthesis-agent.md` provides instructions for an agent that:

1. scans recent conversations for memorable content
2. extracts learnings (facts, patterns, preferences)
3. updates existing memories or creates new ones
4. maintains coherence (resolves conflicts, prunes stale data)
5. evolves personality based on what works

run this as a scheduled agent (daily recommended) to keep memories fresh.

## integration patterns

### session startup
```bash
# search for recent context
qmd search "current" -c memory

# load core personality
qmd get Memory/soul/personality-core.md
```

### during interaction
- note memorable moments (corrections, preferences, explicit requests)
- at natural breakpoints, create memory files
- update relevance for accessed memories

### session end
```bash
# create conversation bridge for continuity
python memory.py close-session <conv_id> "<status>" "<momentum>" "<pending>" "<markers>"
```

## files

- `SKILL.md` - this file
- `scripts/memory.py` - cli for memory operations
- `scripts/synthesis-agent.md` - instructions for scheduled synthesis

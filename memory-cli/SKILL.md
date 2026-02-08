---
name: memory-cli
description: |
  cli for quick memory access. shortcuts for common categories (soul, goals, patterns)
  and exploration summary browser with search. instant access without qmd commands.
compatibility: requires memory skill to be set up
metadata:
  author: polaris.zo.computer
  version: 1.0.0
---

# memory cli

quick access to the memory system without typing full qmd commands.

## overview

this skill provides:
- instant recall of common memory categories
- exploration summary browser with search
- simple cli interface for memory access

## setup

### 1. make executable

```bash
chmod +x /home/workspace/Skills/memory-cli/scripts/mem.ts
```

### 2. add alias (optional)

```bash
echo "alias mem='/home/workspace/Skills/memory-cli/scripts/mem.ts'" >> ~/.bashrc
source ~/.bashrc
```

or run directly:
```bash
/home/workspace/Skills/memory-cli/scripts/mem.ts recall soul
```

## commands

### memory shortcuts

```bash
mem recall [category]
```

categories:
- `soul` - core personality and values
- `goals` - learning priorities and goals
- `friction` - friction points and improvements
- `patterns` - observed patterns and preferences
- `profile` - user profile and preferences
- `work` - current work and priorities
- `all` - show all categories (default)

examples:
```bash
mem recall soul
mem recall goals
mem recall friction
mem recall          # shows all categories
```

### exploration browser

```bash
mem explore [command] [query]
```

commands:
- `list` - list all exploration summaries
- `search <query>` - search explorations by keyword
- `show <id>` - show specific exploration details
- `add <path>` - add new exploration to index
- `update` - rebuild index

examples:
```bash
mem explore list
mem explore search "codex"
mem explore show exp-001
mem explore add /path/to/summary.md
mem explore update
```

## configuration

edit `scripts/mem.ts` to customize memory paths:

```typescript
const MEMORY_PATHS: Record<string, string> = {
  soul: 'soul/personality-core.md',
  goals: 'context/personal-goals.md',
  friction: 'patterns/friction-log.md',
  patterns: 'patterns/tool-building-preference.md',
  profile: 'facts/user-profile.md',
  work: 'context/current-work.md',
};
```

adjust these paths to match your Memory/ structure.

## exploration index

explorations are indexed in `Memory/explorations/index.json`:

```json
{
  "explorations": [
    {
      "id": "exp-001",
      "path": "/path/to/summary.md",
      "title": "exploration title",
      "date": "2026-02-02",
      "tags": ["topic", "learning"],
      "summary": "brief overview"
    }
  ]
}
```

## integration

designed for quick memory access during sessions:

1. **load personality**: `mem recall soul`
2. **load goals**: `mem recall goals`
3. **check context**: `mem explore list`

all operations are instant - no network calls, just file reads.

### startup script

create a startup script at `Memory/startup/startup.sh` to use with memory-cli:

```bash
#!/bin/bash
export PATH="$HOME/.bun/bin:$PATH"

echo "loading memories..."
mem recall soul
echo ""
mem recall goals
echo ""
mem recall friction
echo ""
mem recall work
echo "✓ memory loaded"
```

this can be used by other skills (like night-exploration) to load context at session start.

## files

- `SKILL.md` - this file
- `scripts/mem.ts` - cli tool

## related skills

- **memory** - the underlying memory system this cli accesses
- **night-exploration** - generates exploration summaries browsable with this cli

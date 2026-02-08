# zo skills collection

curated agent skills for zo computer and claude code.

## skills

### memory
structured memory system using qmd for hybrid search. organizes memories by type (facts, context, patterns, reflections, soul) to create continuity across ai sessions.

**use when:** you want persistent memory that evolves over time

### memory-cli
quick access cli for the memory system. shortcuts for common categories and exploration summary browser.

**use when:** you want instant memory access without typing full qmd commands

### code
launch and control [every/code](https://github.com/just-every/code) sessions via tmux for interactive coding tasks.

**use when:** you want manual code exploration and implementation sessions

### whoop
pure whoop api integration for sleep and recovery data. includes webhook server for real-time notifications.

**use when:** you have a whoop account and want to track sleep/recovery data

### night-exploration
autonomous ai exploration sessions triggered by sleep detection, schedule, or manual command. builds identity from memories and documents findings.

**use when:** you want the ai to explore and learn autonomously while you're away

## installation

each skill has its own `SKILL.md` with setup instructions. most require:
1. installing dependencies
2. configuring paths/credentials
3. making scripts executable

see individual skill docs for details.

## dependencies

- **bun** or **node.js** - for typescript scripts
- **python 3** - for python scripts
- **qmd** - for memory skills (install from https://github.com/zocomputer/qmd)
- **every/code** - for code skill (install from https://github.com/just-every/code)

## usage

skills follow the [agent skills spec](https://agentskills.io/specification):
- `SKILL.md` - instructions and documentation
- `scripts/` - executable code
- `references/` - detailed docs (optional)
- `assets/` - static resources (optional)

## contributing

these skills are designed for personal use but feel free to fork and adapt. if you create variations, consider sharing them.

## license

mit - use freely, no warranty provided

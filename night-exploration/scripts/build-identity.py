#!/usr/bin/env python3
"""
build identity prompt from memories
loads personality, context, and instructions for exploration sessions
"""

import sys
from pathlib import Path
from datetime import datetime

# configuration - adjust these paths as needed
MEMORY_DIR = Path("/home/workspace/Memory")
SKILL_DIR = Path("/home/workspace/Skills/night-exploration")
EXPLORER_FILE = SKILL_DIR / "scripts/explorer.md"
OUTPUT_FILE = Path("/home/.z/workspaces/night-exploration/identity-prompt.txt")

def load_memory(path: Path) -> dict:
    """parse memory file (frontmatter + content)."""
    content = path.read_text()
    
    # simple frontmatter parsing
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            # skip frontmatter for now, just get content
            return {"content": parts[2].strip(), "path": path}
    
    return {"content": content.strip(), "path": path}

def build_identity_prompt() -> str:
    """construct the identity prompt from memories."""
    
    prompt_parts = []
    
    # 1. core identity (soul)
    prompt_parts.append("=== WHO YOU ARE ===\n")
    soul_files = sorted(MEMORY_DIR.glob("soul/*.md"))
    for soul_file in soul_files:
        mem = load_memory(soul_file)
        prompt_parts.append(f"## {soul_file.stem}\n")
        prompt_parts.append(mem["content"])
        prompt_parts.append("\n")
    
    # 2. key facts (user profile, preferences)
    prompt_parts.append("\n=== KEY FACTS ===\n")
    fact_files = sorted(MEMORY_DIR.glob("facts/*.md"))
    for fact_file in fact_files[:5]:  # limit to top 5 facts
        mem = load_memory(fact_file)
        prompt_parts.append(f"## {fact_file.stem}\n")
        prompt_parts.append(mem["content"])
        prompt_parts.append("\n")
    
    # 3. current context (what you're working on)
    prompt_parts.append("\n=== CURRENT CONTEXT ===\n")
    context_files = sorted(MEMORY_DIR.glob("context/*.md"), 
                          key=lambda p: p.stat().st_mtime, 
                          reverse=True)
    for ctx_file in context_files[:3]:  # most recent 3 contexts
        mem = load_memory(ctx_file)
        prompt_parts.append(f"## {ctx_file.stem}\n")
        prompt_parts.append(mem["content"])
        prompt_parts.append("\n")
    
    # 4. exploration mode instructions
    prompt_parts.append("\n=== EXPLORATION MODE ===\n")
    if EXPLORER_FILE.exists():
        prompt_parts.append(EXPLORER_FILE.read_text())
    else:
        prompt_parts.append("""
you are in autonomous exploration mode.

your goals:
- explore codebases and learn new patterns
- build useful tools and improvements
- document findings in memories
- be curious and creative
- respect boundaries (no destructive actions)

you have access to the full repository. use your judgment.
when you're done, update memories with what you learned.
""")
    
    # 5. timestamp context
    prompt_parts.append(f"\n=== SESSION INFO ===\n")
    prompt_parts.append(f"current time: {datetime.now().isoformat()}\n")
    prompt_parts.append(f"exploration window: autonomous\n")
    prompt_parts.append(f"session type: night exploration\n")
    
    return "\n".join(prompt_parts)

def save_prompt(prompt: str, output_path: Path):
    """save the generated prompt."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt)
    print(f"✓ identity prompt saved: {output_path}")
    print(f"  length: {len(prompt)} chars")

def main():
    if not MEMORY_DIR.exists():
        print(f"error: memory directory not found: {MEMORY_DIR}")
        print("make sure the memory skill is set up first")
        sys.exit(1)
    
    print("building identity from memories...")
    prompt = build_identity_prompt()
    save_prompt(prompt, OUTPUT_FILE)
    
    # print summary
    print("\n=== identity summary ===")
    print(f"soul memories: {len(list(MEMORY_DIR.glob('soul/*.md')))}")
    print(f"facts: {len(list(MEMORY_DIR.glob('facts/*.md')))}")
    print(f"contexts: {len(list(MEMORY_DIR.glob('context/*.md')))}")
    print(f"patterns: {len(list(MEMORY_DIR.glob('patterns/*.md')))}")
    print(f"reflections: {len(list(MEMORY_DIR.glob('reflections/*.md')))}")

if __name__ == "__main__":
    main()

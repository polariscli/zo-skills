#!/usr/bin/env python3
"""
memory management cli
create, search, update, and maintain the living memory system.
"""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# ensure qmd is in PATH
os.environ["PATH"] = f"{Path.home()}/.bun/bin:" + os.environ.get("PATH", "")

MEMORY_ROOT = Path("/home/workspace/Memory")
MEMORY_TYPES = ["facts", "context", "patterns", "reflections", "soul"]
QMD_COLLECTION = "memory"

def ensure_memory_dirs():
    """ensure all memory directories exist."""
    for mem_type in MEMORY_TYPES:
        (MEMORY_ROOT / mem_type).mkdir(parents=True, exist_ok=True)

def parse_frontmatter(content: str) -> tuple[Dict, str]:
    """extract frontmatter and body from markdown."""
    if not content.startswith("---\n"):
        return {}, content
    
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_str = parts[1]
    body = parts[2]
    
    # simple yaml parsing for our needs
    frontmatter = {}
    for line in frontmatter_str.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # parse lists
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip('"\'') for v in value[1:-1].split(",")]
            # parse booleans
            elif value.lower() in ["true", "false"]:
                value = value.lower() == "true"
            
            frontmatter[key] = value
    
    return frontmatter, body

def parse_date_str(value: str) -> Optional[datetime]:
    """parse yyyy-mm-dd date string."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None

def normalize_tags(value) -> List[str]:
    """normalize tags into a list of strings."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [t.strip() for t in value.split(",") if t.strip()]
    return []

def format_frontmatter(fm: Dict) -> str:
    """format frontmatter dict as yaml."""
    lines = []
    for key, value in fm.items():
        if isinstance(value, list):
            formatted = "[" + ", ".join(f'"{v}"' for v in value) + "]"
        elif isinstance(value, bool):
            formatted = str(value).lower()
        else:
            formatted = str(value)
        lines.append(f"{key}: {formatted}")
    return "\n".join(lines)

def create_memory_file(
    mem_type: str,
    name: str,
    content: str,
    tags: List[str],
    importance: str = "medium",
    related: List[str] = None,
    conversation_id: Optional[str] = None,
    priority: Optional[str] = None
) -> Path:
    """create a new memory file."""
    ensure_memory_dirs()
    
    if mem_type not in MEMORY_TYPES:
        raise ValueError(f"invalid memory type: {mem_type}")
    
    # sanitize filename
    filename = re.sub(r'[^\w\s-]', '', name.lower())
    filename = re.sub(r'[-\s]+', '-', filename)
    filepath = MEMORY_ROOT / mem_type / f"{filename}.md"
    
    now = datetime.now().strftime("%Y-%m-%d")
    
    frontmatter = {
        "type": mem_type,
        "tags": tags,
        "created": now,
        "last_accessed": now,
        "importance": importance,
    }
    
    if related:
        frontmatter["related"] = related
    
    if conversation_id:
        frontmatter["conversation_id"] = conversation_id
    
    if priority:
        frontmatter["priority"] = priority
    
    full_content = f"""---
{format_frontmatter(frontmatter)}
---

{content}
"""
    
    filepath.write_text(full_content)
    print(f"✓ created memory: {filepath.relative_to('/home/workspace')}")
    
    return filepath

def search_memories(
    query: str,
    semantic: bool = False,
    min_score: Optional[float] = None,
    limit: int = 5,
    show_scores: bool = False
) -> List[Dict]:
    """
    search memories using qmd.

    returns list of dicts with keys: path, score, context
    """
    cmd = ["qmd"]
    if semantic:
        cmd.append("vsearch")
    else:
        cmd.append("search")
    cmd.extend([query, "-c", QMD_COLLECTION])

    # add flags
    if min_score is not None:
        cmd.extend(["--min-score", str(min_score)])
    cmd.extend(["-n", str(limit)])

    # use --files to get scores
    if show_scores or min_score is not None:
        cmd.append("--files")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"error searching: {result.stderr}")
        return []

    # parse output
    matches = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue

        # --files format: docid,score,filepath,context
        if show_scores or min_score is not None:
            parts = line.split(",", 3)
            if len(parts) >= 3:
                matches.append({
                    "path": parts[2],
                    "score": float(parts[1]),
                    "context": parts[3] if len(parts) > 3 else ""
                })
        else:
            # default format: just paths
            matches.append({
                "path": line,
                "score": None,
                "context": ""
            })

    return matches

def get_memory(filepath: str) -> str:
    """retrieve full memory content."""
    result = subprocess.run(
        ["qmd", "get", filepath],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"error retrieving memory: {result.stderr}")
        return ""
    
    return result.stdout

def update_memory(filepath: Path, updates: Dict):
    """update memory frontmatter."""
    if not filepath.exists():
        print(f"memory not found: {filepath}")
        return
    
    content = filepath.read_text()
    frontmatter, body = parse_frontmatter(content)
    
    # update fields
    frontmatter.update(updates)
    frontmatter["last_accessed"] = datetime.now().strftime("%Y-%m-%d")
    
    new_content = f"""---
{format_frontmatter(frontmatter)}
---

{body}"""
    
    filepath.write_text(new_content)
    print(f"✓ updated: {filepath.relative_to(Path.home() / 'workspace')}")

def list_recent_memories(days: int = 7) -> List[Path]:
    """list memories created or accessed in last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    
    for mem_type in MEMORY_TYPES:
        type_dir = MEMORY_ROOT / mem_type
        if not type_dir.exists():
            continue
        
        for filepath in type_dir.glob("*.md"):
            content = filepath.read_text()
            frontmatter, _ = parse_frontmatter(content)
            
            dates = []
            if "created" in frontmatter:
                try:
                    dates.append(datetime.strptime(frontmatter["created"], "%Y-%m-%d"))
                except:
                    pass
            if "last_accessed" in frontmatter:
                try:
                    dates.append(datetime.strptime(frontmatter["last_accessed"], "%Y-%m-%d"))
                except:
                    pass
            
            if any(d >= cutoff for d in dates):
                recent.append((filepath, frontmatter))
    
    return sorted(recent, key=lambda x: x[1].get("last_accessed", ""), reverse=True)

def get_latest_synthesis_date() -> Optional[datetime]:
    """find the latest synthesis reflection date."""
    reflections_dir = MEMORY_ROOT / "reflections"
    if not reflections_dir.exists():
        return None

    latest = None
    for filepath in reflections_dir.glob("*.md"):
        content = filepath.read_text()
        frontmatter, _ = parse_frontmatter(content)
        tags = normalize_tags(frontmatter.get("tags", []))
        if "synthesis" not in tags:
            continue

        created = parse_date_str(frontmatter.get("created", ""))
        if not created:
            match = re.search(r"\d{4}-\d{2}-\d{2}", filepath.name)
            if match:
                created = parse_date_str(match.group(0))

        if created and (latest is None or created > latest):
            latest = created

    return latest

def list_changed_memories(since_date: datetime) -> List[Dict]:
    """list memories created or accessed since a date."""
    changes = []

    for mem_type in MEMORY_TYPES:
        type_dir = MEMORY_ROOT / mem_type
        if not type_dir.exists():
            continue

        for filepath in type_dir.glob("*.md"):
            content = filepath.read_text()
            frontmatter, _ = parse_frontmatter(content)

            created = parse_date_str(frontmatter.get("created", ""))
            last_accessed = parse_date_str(frontmatter.get("last_accessed", ""))

            last_change = max([d for d in [created, last_accessed] if d], default=None)
            if not last_change:
                continue

            if last_change >= since_date:
                mem_type_value = frontmatter.get("type", mem_type)
                if mem_type_value not in MEMORY_TYPES:
                    mem_type_value = mem_type
                changes.append({
                    "path": filepath,
                    "type": mem_type_value,
                    "created": created,
                    "last_accessed": last_accessed,
                    "last_change": last_change,
                })

    return sorted(changes, key=lambda x: x["last_change"], reverse=True)

def get_stats():
    """get memory system statistics."""
    stats = {mem_type: 0 for mem_type in MEMORY_TYPES}
    total = 0
    
    for mem_type in MEMORY_TYPES:
        type_dir = MEMORY_ROOT / mem_type
        if type_dir.exists():
            count = len(list(type_dir.glob("*.md")))
            stats[mem_type] = count
            total += count
    
    return stats, total

def get_related_memories(
    filepath: str,
    min_score: float = 0.7,
    limit: int = 5
) -> List[Dict]:
    """
    find memories related to a specific memory.
    
    uses both:
    - semantic similarity (content-based)
    - explicit relationships (frontmatter 'related' field)
    """
    # resolve path
    memory_path = Path(filepath)
    if not memory_path.is_absolute():
        memory_path = MEMORY_ROOT / filepath
    
    if not memory_path.exists():
        print(f"memory not found: {memory_path}")
        return []
    
    # read memory content
    content = memory_path.read_text()
    frontmatter, body = parse_frontmatter(content)
    
    # find semantic matches using body as query
    semantic_matches = search_memories(
        query=body[:500],  # use first 500 chars to avoid query length issues
        semantic=True,
        min_score=min_score,
        limit=limit * 2,  # get more to filter self out
        show_scores=True
    )
    
    # filter out the source memory itself
    self_path_str = str(memory_path)
    semantic_matches = [
        m for m in semantic_matches 
        if not m["path"].endswith(memory_path.name) and m["path"] != self_path_str
    ][:limit]
    
    # get explicit relationships from frontmatter
    explicit_related = []
    if "related" in frontmatter:
        related_paths = frontmatter["related"]
        if isinstance(related_paths, str):
            related_paths = [related_paths]
        
        for rel_path in related_paths:
            rel_memory_path = MEMORY_ROOT / rel_path
            if rel_memory_path.exists():
                explicit_related.append({
                    "path": str(rel_memory_path),
                    "score": 1.0,  # explicit relationship
                    "relationship": "explicit"
                })
    
    # combine results, prioritizing explicit relationships
    all_related = explicit_related + semantic_matches
    
    return all_related

def health_check() -> Dict:
    """
    verify memory system health.
    
    checks:
    - qmd accessibility
    - memory directories
    - qmd collection initialization
    - embedding functionality
    - disk usage
    """
    health = {
        "qmd_accessible": False,
        "qmd_version": None,
        "directories_exist": False,
        "collection_initialized": False,
        "embeddings_work": False,
        "disk_usage_mb": 0,
        "errors": []
    }
    
    # check qmd accessibility
    try:
        result = subprocess.run(
            ["qmd", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            health["qmd_accessible"] = True
            health["qmd_version"] = result.stdout.strip()
    except Exception as e:
        health["errors"].append(f"qmd not accessible: {e}")
    
    # check memory directories
    missing_dirs = []
    for mem_type in MEMORY_TYPES:
        type_dir = MEMORY_ROOT / mem_type
        if not type_dir.exists():
            missing_dirs.append(mem_type)
    
    health["directories_exist"] = len(missing_dirs) == 0
    if missing_dirs:
        health["errors"].append(f"missing directories: {', '.join(missing_dirs)}")
    
    # check qmd collection
    try:
        result = subprocess.run(
            ["qmd", "collection", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if QMD_COLLECTION in result.stdout:
            health["collection_initialized"] = True
        else:
            health["errors"].append(f"collection '{QMD_COLLECTION}' not found")
    except Exception as e:
        health["errors"].append(f"cannot check collections: {e}")
    
    # check embeddings with a simple search
    try:
        result = subprocess.run(
            ["qmd", "vsearch", "test", "-c", QMD_COLLECTION, "-n", "1"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            health["embeddings_work"] = True
        else:
            health["errors"].append(f"embeddings check failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        health["errors"].append("embeddings check timed out (may need embedding)")
    except Exception as e:
        health["errors"].append(f"cannot check embeddings: {e}")
    
    # check disk usage
    try:
        result = subprocess.run(
            ["du", "-sm", str(MEMORY_ROOT)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            size_str = result.stdout.split()[0]
            health["disk_usage_mb"] = int(size_str)
    except Exception as e:
        health["errors"].append(f"cannot check disk usage: {e}")
    
    return health

def cmd_create(args):
    """create new memory."""
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    related = [r.strip() for r in args.related.split(",")] if args.related else None
    
    create_memory_file(
        mem_type=args.type,
        name=args.name,
        content=args.content,
        tags=tags,
        importance=args.importance,
        related=related,
        conversation_id=args.conversation_id if hasattr(args, 'conversation_id') and args.conversation_id else None,
        priority=args.priority if hasattr(args, 'priority') and args.priority else None
    )

def cmd_search(args):
    """search memories."""
    results = search_memories(
        query=args.query,
        semantic=args.semantic,
        min_score=args.min_score if hasattr(args, 'min_score') else None,
        limit=args.limit if hasattr(args, 'limit') else 5,
        show_scores=args.show_scores if hasattr(args, 'show_scores') else False
    )

    if not results:
        print("no memories found")
        return

    search_type = "semantic " if args.semantic else ""
    print(f"🔍 found {len(results)} {search_type}match(es):\n")

    for result in results:
        if result.get("score") is not None:
            score_str = f"[{result['score']:.3f}]"
            print(f"  {score_str} {result['path']}")
            if result.get("context"):
                print(f"      {result['context'][:100]}")
        else:
            print(f"  {result['path']}")

def cmd_get(args):
    """retrieve memory."""
    content = get_memory(args.path)
    if content:
        print(content)

def cmd_update(args):
    """update memory metadata."""
    filepath = Path(args.path)
    if not filepath.is_absolute():
        filepath = Path.home() / "workspace" / filepath
    
    updates = {}
    if args.importance:
        updates["importance"] = args.importance
    if args.tags:
        updates["tags"] = [t.strip() for t in args.tags.split(",")]
    if args.add_tag:
        content = filepath.read_text()
        fm, _ = parse_frontmatter(content)
        existing_tags = fm.get("tags", [])
        if args.add_tag not in existing_tags:
            existing_tags.append(args.add_tag)
        updates["tags"] = existing_tags
    
    update_memory(filepath, updates)

def cmd_review(args):
    """review recent memories."""
    recent = list_recent_memories(args.days)
    
    if not recent:
        print(f"no memories from last {args.days} days")
        return
    
    print(f"📋 memories from last {args.days} days:\n")
    for filepath, frontmatter in recent:
        rel_path = filepath.relative_to(MEMORY_ROOT)
        mem_type = frontmatter.get("type", "unknown")
        importance = frontmatter.get("importance", "medium")
        tags = ", ".join(frontmatter.get("tags", []))
        
        print(f"  [{mem_type}] {rel_path}")
        print(f"    importance: {importance}")
        if tags:
            print(f"    tags: {tags}")
        print()

def cmd_changes(args):
    """show memories changed since a date."""
    if args.since_last_synthesis:
        since_date = get_latest_synthesis_date()
        if not since_date:
            print("no synthesis reflections found")
            return
    elif args.since:
        since_date = parse_date_str(args.since)
        if not since_date:
            print("invalid --since date (expected YYYY-MM-DD)")
            return
    else:
        since_date = datetime.now() - timedelta(days=args.days)

    changes = list_changed_memories(since_date)
    since_str = since_date.strftime("%Y-%m-%d")

    if not changes:
        print(f"no memory changes since {since_str}")
        return

    print(f"🧭 memory changes since {since_str}:\n")

    counts = {mem_type: 0 for mem_type in MEMORY_TYPES}
    for item in changes:
        counts[item["type"]] = counts.get(item["type"], 0) + 1

    print("summary:")
    total = 0
    for mem_type in MEMORY_TYPES:
        count = counts.get(mem_type, 0)
        total += count
        print(f"  {mem_type:15} {count:3} changes")
    print(f"  total:          {total:3} changes\n")

    print("changed memories:\n")
    for item in changes:
        rel_path = item["path"].relative_to(MEMORY_ROOT)
        created = item["created"].strftime("%Y-%m-%d") if item["created"] else "unknown"
        last_accessed = item["last_accessed"].strftime("%Y-%m-%d") if item["last_accessed"] else "unknown"
        last_change = item["last_change"].strftime("%Y-%m-%d")

        print(f"  [{item['type']}] {rel_path}")
        print(f"    last_change:  {last_change}")
        print(f"    created:      {created}")
        print(f"    last_accessed: {last_accessed}")
        print()

def cmd_stats(args):
    """show memory statistics."""
    stats, total = get_stats()
    
    print("🧠 memory system stats:\n")
    for mem_type, count in stats.items():
        print(f"  {mem_type:15} {count:3} memories")
    print(f"\n  total:          {total:3} memories")

def cmd_consolidate(args):
    """consolidate related memories (manual review helper)."""
    print("🔄 consolidation suggestions:\n")
    
    # find memories with similar tags
    tag_groups = {}
    for mem_type in MEMORY_TYPES:
        type_dir = MEMORY_ROOT / mem_type
        if not type_dir.exists():
            continue
        
        for filepath in type_dir.glob("*.md"):
            content = filepath.read_text()
            frontmatter, _ = parse_frontmatter(content)
            tags = frontmatter.get("tags", [])
            
            for tag in tags:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(filepath.relative_to(MEMORY_ROOT))
    
    # show groups with multiple memories
    for tag, files in sorted(tag_groups.items()):
        if len(files) > 1:
            print(f"  tag '{tag}' ({len(files)} memories):")
            for f in files:
                print(f"    - {f}")
            print()

def cmd_close_session(args):
    """create a conversation bridge memory."""
    conv_id = args.conv_id
    status = args.status
    momentum = args.momentum
    pending = args.pending
    markers = args.markers

    # create content
    content = f"""---
type: conversation_bridge
---
# Conversation Bridge: {conv_id}

## STATUS
{status}

## MOMENTUM
{momentum}

## PENDING
{pending}

## RETRIEVAL-MARKERS
{markers}
"""

    # create filename
    conv_id_last_8 = conv_id[-8:]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"bridge-{conv_id_last_8}-{timestamp}.md"

    # create file
    filepath = MEMORY_ROOT / "context" / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)
    print(f"✓ created conversation bridge: {filepath.relative_to('/home/workspace')}")
    return filepath

def format_memory_content(
    raw_content: str,
    memory_type: str,
    topic: str,
    context: Optional[Dict] = None
) -> tuple[str, Dict]:
    """
    format memory for optimal retrieval.

    principles:
    - front-load critical information (first 50 chars matter most)
    - include diverse terminology for retrieval
    - add temporal and relational context
    - balance high-level and specific details

    returns: (formatted_content, frontmatter_dict)
    """
    now = datetime.now().strftime("%Y-%m-%d")
    context = context or {}

    # type-specific formatting templates
    if memory_type == "preference":
        formatted = f"PREFERENCE - {topic}: {raw_content[:200]}. Noted {now}. Applies to similar situations and related decisions."
        fm = {
            "type": "preference",
            "tags": [topic.lower(), "preference", context.get("user_name", "user")],
            "created": now,
            "last_accessed": now,
            "importance": context.get("importance", "medium"),
        }

    elif memory_type == "technical":
        formatted = f"TECHNICAL - {topic}: {raw_content[:200]}. Documented {now} for future reference and troubleshooting."
        fm = {
            "type": "technical",
            "tags": [topic.lower(), "technical", "reference"],
            "created": now,
            "last_accessed": now,
            "importance": context.get("importance", "medium"),
        }

    elif memory_type == "decision":
        formatted = f"DECISION - {topic}: {raw_content[:200]}. Decided {now}. Context: {context.get('decision_context', 'project evolution')}."
        fm = {
            "type": "decision",
            "tags": [topic.lower(), "decision", "rationale"],
            "created": now,
            "last_accessed": now,
            "importance": context.get("importance", "high"),
        }

    elif memory_type == "project":
        status = context.get("status", "active")
        formatted = f"PROJECT - {topic} [{status}]: {raw_content[:200]}. Last updated {now}."
        fm = {
            "type": "project",
            "tags": [topic.lower(), "project", status],
            "created": now,
            "last_accessed": now,
            "importance": context.get("importance", "high"),
        }

    elif memory_type == "pattern":
        formatted = f"PATTERN - {topic}: {raw_content[:200]}. Observed {now}. Generalizes to similar contexts."
        fm = {
            "type": "pattern",
            "tags": [topic.lower(), "pattern", "learning"],
            "created": now,
            "last_accessed": now,
            "importance": context.get("importance", "medium"),
        }

    elif memory_type == "conversation_bridge":
        formatted = f"BRIDGE - {topic}: {raw_content[:200]}. Created {now} for session continuity."
        fm = {
            "type": "conversation_bridge",
            "tags": ["bridge", "continuity", topic.lower()],
            "created": now,
            "last_accessed": now,
            "importance": "high",
        }

    elif memory_type == "consciousness":
        formatted = f"CONSCIOUSNESS - {topic}: {raw_content[:200]}. Reflected {now}."
        fm = {
            "type": "consciousness",
            "tags": [topic.lower(), "self-awareness", "meta"],
            "created": now,
            "last_accessed": now,
            "importance": "medium",
        }

    elif memory_type == "meta_pattern":
        formatted = f"META-PATTERN - {topic}: {raw_content[:200]}. Identified {now}. Applies across multiple contexts."
        fm = {
            "type": "meta_pattern",
            "tags": [topic.lower(), "meta-pattern", "high-level"],
            "created": now,
            "last_accessed": now,
            "importance": "high",
        }

    elif memory_type == "principle":
        formatted = f"PRINCIPLE - {topic}: {raw_content[:200]}. Established {now}. Foundational for future decisions."
        fm = {
            "type": "principle",
            "tags": [topic.lower(), "principle", "core"],
            "created": now,
            "last_accessed": now,
            "importance": "critical",
        }

    else:
        # generic fallback
        formatted = f"{topic}: {raw_content[:200]}. Noted {now}."
        fm = {
            "type": memory_type,
            "tags": [topic.lower()],
            "created": now,
            "last_accessed": now,
            "importance": context.get("importance", "medium"),
        }

    return formatted, fm

def cmd_format(args):
    """format memory content for optimal retrieval."""
    context = {}
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            print("error: invalid json in --context")
            return

    formatted_content, frontmatter = format_memory_content(
        raw_content=args.content,
        memory_type=args.type,
        topic=args.topic,
        context=context
    )

    print("✓ formatted memory:\n")
    print("frontmatter:")
    print(format_frontmatter(frontmatter))
    print("\ncontent:")
    print(formatted_content)

    if args.create:
        # create the memory file
        mem_type_dir = args.type
        if args.type in ["preference", "technical", "decision", "principle"]:
            mem_type_dir = "facts"
        elif args.type == "project":
            mem_type_dir = "context"
        elif args.type in ["pattern", "meta_pattern", "consciousness"]:
            mem_type_dir = "patterns"
        elif args.type == "conversation_bridge":
            mem_type_dir = "context"

        # sanitize filename
        filename = re.sub(r'[^\w\s-]', '', args.topic.lower())
        filename = re.sub(r'[-\s]+', '-', filename)
        filepath = MEMORY_ROOT / mem_type_dir / f"{filename}.md"

        full_content = f"""---
{format_frontmatter(frontmatter)}
---

{formatted_content}
"""

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(full_content)
        print(f"\n✓ created memory file: {filepath.relative_to('/home/workspace')}")

def cmd_related(args):
    """find related memories."""
    related = get_related_memories(
        filepath=args.path,
        min_score=args.min_score,
        limit=args.limit
    )
    
    if not related:
        print("no related memories found")
        return
    
    print(f"🔗 found {len(related)} related memor(y/ies):\n")
    
    for item in related:
        relationship = item.get("relationship", "semantic")
        score = item["score"]
        path = item["path"]
        
        if relationship == "explicit":
            print(f"  [explicit] {path}")
        else:
            print(f"  [{score:.3f}] {path}")

def cmd_health(args):
    """check memory system health."""
    health = health_check()
    
    print("🏥 memory system health check:\n")
    
    # qmd
    status = "✓" if health["qmd_accessible"] else "✗"
    print(f"  {status} qmd accessible: {health['qmd_accessible']}")
    if health["qmd_version"]:
        print(f"      version: {health['qmd_version']}")
    
    # directories
    status = "✓" if health["directories_exist"] else "✗"
    print(f"  {status} directories exist: {health['directories_exist']}")
    
    # collection
    status = "✓" if health["collection_initialized"] else "✗"
    print(f"  {status} collection initialized: {health['collection_initialized']}")
    
    # embeddings
    status = "✓" if health["embeddings_work"] else "✗"
    print(f"  {status} embeddings work: {health['embeddings_work']}")
    
    # disk usage
    print(f"  📊 disk usage: {health['disk_usage_mb']} MB")
    
    # errors
    if health["errors"]:
        print(f"\n  ⚠️  errors:")
        for error in health["errors"]:
            print(f"      - {error}")
    else:
        print(f"\n  ✓ no errors detected")

def main():
    parser = argparse.ArgumentParser(description="memory management cli")
    subparsers = parser.add_subparsers(dest="command", help="command")
    
    # create command
    create_parser = subparsers.add_parser("create", help="create new memory")
    create_parser.add_argument("--type", required=True, choices=MEMORY_TYPES)
    create_parser.add_argument("--name", required=True, help="memory name")
    create_parser.add_argument("--content", required=True, help="memory content")
    create_parser.add_argument("--tags", help="comma-separated tags")
    create_parser.add_argument("--importance", default="medium", choices=["low", "medium", "high", "critical"])
    create_parser.add_argument("--related", help="comma-separated related memory paths")
    create_parser.add_argument("--conversation-id", help="conversation id for tracking")
    create_parser.add_argument("--priority", choices=["low", "medium", "high", "urgent"], help="priority level")
    create_parser.set_defaults(func=cmd_create)
    
    # search command
    search_parser = subparsers.add_parser("search", help="search memories")
    search_parser.add_argument("query", help="search query")
    search_parser.add_argument("--semantic", action="store_true", help="use semantic search")
    search_parser.add_argument("--min-score", type=float, help="minimum similarity score (0.0-1.0, recommended >= 0.7)")
    search_parser.add_argument("--limit", type=int, default=5, help="number of results (default: 5)")
    search_parser.add_argument("--show-scores", action="store_true", help="display similarity scores")
    search_parser.set_defaults(func=cmd_search)
    
    # get command
    get_parser = subparsers.add_parser("get", help="retrieve memory")
    get_parser.add_argument("path", help="memory path")
    get_parser.set_defaults(func=cmd_get)
    
    # update command
    update_parser = subparsers.add_parser("update", help="update memory")
    update_parser.add_argument("path", help="memory path")
    update_parser.add_argument("--importance", choices=["low", "medium", "high", "critical"])
    update_parser.add_argument("--tags", help="replace tags (comma-separated)")
    update_parser.add_argument("--add-tag", help="add single tag")
    update_parser.set_defaults(func=cmd_update)
    
    # review command
    review_parser = subparsers.add_parser("review", help="review recent memories")
    review_parser.add_argument("--days", type=int, default=7, help="days to review (default: 7)")
    review_parser.set_defaults(func=cmd_review)

    # changes command
    changes_parser = subparsers.add_parser("changes", help="show memories changed since a date")
    changes_group = changes_parser.add_mutually_exclusive_group()
    changes_group.add_argument("--since", help="start date (YYYY-MM-DD)")
    changes_group.add_argument("--since-last-synthesis", action="store_true", help="use latest synthesis reflection date")
    changes_parser.add_argument("--days", type=int, default=7, help="days to look back (default: 7)")
    changes_parser.set_defaults(func=cmd_changes)
    
    # stats command
    stats_parser = subparsers.add_parser("stats", help="show statistics")
    stats_parser.set_defaults(func=cmd_stats)
    
    # consolidate command
    consolidate_parser = subparsers.add_parser("consolidate", help="find consolidation opportunities")
    consolidate_parser.set_defaults(func=cmd_consolidate)
    
    # close-session command
    close_session_parser = subparsers.add_parser("close-session", help="create a conversation bridge memory")
    close_session_parser.add_argument("conv_id", help="conversation id")
    close_session_parser.add_argument("status", help="status summary")
    close_session_parser.add_argument("momentum", help="momentum summary")
    close_session_parser.add_argument("pending", help="pending tasks")
    close_session_parser.add_argument("markers", help="retrieval markers")
    close_session_parser.set_defaults(func=cmd_close_session)

    # format command
    format_parser = subparsers.add_parser("format", help="format memory for optimal retrieval")
    format_parser.add_argument("--type", required=True,
                              choices=["preference", "technical", "decision", "project",
                                      "pattern", "conversation_bridge", "consciousness",
                                      "meta_pattern", "principle"],
                              help="memory type")
    format_parser.add_argument("--topic", required=True, help="memory topic/subject")
    format_parser.add_argument("--content", required=True, help="raw memory content")
    format_parser.add_argument("--context", help="json context (user_name, importance, status, etc.)")
    format_parser.add_argument("--create", action="store_true", help="create memory file after formatting")
    format_parser.set_defaults(func=cmd_format)

    # related command
    related_parser = subparsers.add_parser("related", help="find related memories")
    related_parser.add_argument("path", help="memory file path")
    related_parser.add_argument("--min-score", type=float, default=0.7, help="minimum similarity score (default: 0.7)")
    related_parser.add_argument("--limit", type=int, default=5, help="number of results (default: 5)")
    related_parser.set_defaults(func=cmd_related)
    
    # health command
    health_parser = subparsers.add_parser("health", help="check memory system health")
    health_parser.set_defaults(func=cmd_health)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)

if __name__ == "__main__":
    main()

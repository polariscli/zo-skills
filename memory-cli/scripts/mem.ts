#!/usr/bin/env bun
/**
 * memory cli - quick access to memory system
 * provides shortcuts for common memory categories and exploration browsing
 */

import { readFileSync, writeFileSync, existsSync, readdirSync } from 'fs';
import { join } from 'path';

// configuration - adjust these paths to match your setup
const MEMORY_ROOT = '/home/workspace/Memory';
const EXPLORATIONS_DIR = '/home/workspace/Memory/explorations';
const INDEX_FILE = join(EXPLORATIONS_DIR, 'index.json');

// memory shortcuts mapping - customize these for your memory structure
const MEMORY_PATHS: Record<string, string> = {
  soul: 'soul/personality-core.md',
  goals: 'context/personal-goals.md',
  friction: 'patterns/friction-log.md',
  patterns: 'patterns/tool-building-preference.md',
  profile: 'facts/user-profile.md',
  work: 'context/2026-02-current-work.md',
};

// terminal colors
const colors = {
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  gray: '\x1b[90m',
  reset: '\x1b[0m',
};

function color(text: string, c: keyof typeof colors): string {
  return `${colors[c]}${text}${colors.reset}`;
}

// read markdown file and extract content (skip frontmatter)
function readMarkdown(path: string): string | null {
  try {
    const fullPath = join(MEMORY_ROOT, path);
    const content = readFileSync(fullPath, 'utf-8');
    const match = content.match(/---[\s\S]*?---([\s\S]*)/);
    return match ? match[1].trim() : content;
  } catch (e) {
    return null;
  }
}

// show a memory category
function showCategory(category: string): boolean {
  if (category === 'all') {
    let found = false;
    for (const cat of Object.keys(MEMORY_PATHS)) {
      const content = readMarkdown(MEMORY_PATHS[cat]);
      if (content) {
        console.log(`\n${color('━━━ ' + cat.toUpperCase() + ' ━━━', 'cyan')}`);
        console.log(content);
        found = true;
      }
    }
    return found;
  }

  const path = MEMORY_PATHS[category];
  if (!path) {
    console.log(color(`unknown category: ${category}`, 'yellow'));
    console.log(color(`available: ${Object.keys(MEMORY_PATHS).join(', ')}, all`, 'gray'));
    return false;
  }

  const content = readMarkdown(path);
  if (!content) {
    console.log(color(`category not found: ${category}`, 'yellow'));
    console.log(color(`expected file: ${join(MEMORY_ROOT, path)}`, 'gray'));
    return false;
  }

  console.log(content);
  return true;
}

// exploration index types
interface Exploration {
  id: string;
  path: string;
  title: string;
  date: string;
  tags: string[];
  summary: string;
}

interface ExplorationIndex {
  explorations: Exploration[];
  lastUpdated: string;
}

// load or create index
function getIndex(): ExplorationIndex {
  if (existsSync(INDEX_FILE)) {
    return JSON.parse(readFileSync(INDEX_FILE, 'utf-8'));
  }
  return { explorations: [], lastUpdated: new Date().toISOString() };
}

// save index
function saveIndex(index: ExplorationIndex): void {
  writeFileSync(INDEX_FILE, JSON.stringify(index, null, 2));
}

// parse frontmatter from markdown
function parseFrontmatter(content: string): Record<string, any> | null {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;

  const frontmatter: Record<string, any> = {};
  for (const line of match[1].split('\n')) {
    const [key, ...valueParts] = line.split(':');
    if (key && valueParts.length > 0) {
      const value = valueParts.join(':').trim().replace(/^"(.*)"$/, '$1').replace(/^'(.*)'$/, '$1');
      if (value.includes('[')) {
        const arrayMatch = value.match(/\[(.*?)\]/);
        if (arrayMatch) {
          frontmatter[key.trim()] = arrayMatch[1].split(',').map(v => v.trim().replace(/^"(.*)"$/, '$1'));
        }
      } else {
        frontmatter[key.trim()] = value;
      }
    }
  }
  return frontmatter;
}

// add exploration to index
function addExploration(path: string): boolean {
  try {
    const content = readFileSync(path, 'utf-8');
    const frontmatter = parseFrontmatter(content);

    if (!frontmatter) {
      console.log(color('no frontmatter found in file', 'yellow'));
      return false;
    }

    const id = frontmatter.id || `exp-${Date.now()}`;
    const index = getIndex();

    if (index.explorations.find(e => e.id === id)) {
      console.log(color(`exploration ${id} already indexed`, 'yellow'));
      return true;
    }

    index.explorations.push({
      id,
      path,
      title: frontmatter.title || 'Untitled',
      date: frontmatter.date || new Date().toISOString().split('T')[0],
      tags: frontmatter.tags || [],
      summary: frontmatter.summary || '',
    });

    index.lastUpdated = new Date().toISOString();
    saveIndex(index);

    console.log(color(`indexed: ${id}`, 'green'));
    return true;
  } catch (e) {
    console.log(color(`failed to index: ${(e as Error).message}`, 'yellow'));
    return false;
  }
}

// list explorations
function listExplorations(): void {
  const index = getIndex();
  
  if (index.explorations.length === 0) {
    console.log(color('no explorations indexed', 'gray'));
    console.log(color('use: mem explore add <path> to add explorations', 'gray'));
    return;
  }

  console.log(color(`\nexplorations (${index.explorations.length}):`, 'cyan'));
  
  for (const exp of index.explorations) {
    const tags = exp.tags.length > 0 ? color(`[${exp.tags.join(', ')}]`, 'gray') : '';
    console.log(`  ${color(exp.id, 'green')} - ${exp.title} ${color(exp.date, 'gray')} ${tags}`);
  }
}

// search explorations
function searchExplorations(query: string): void {
  const index = getIndex();
  const q = query.toLowerCase();

  const results = index.explorations.filter(exp => 
    exp.title.toLowerCase().includes(q) ||
    exp.tags.some(t => t.toLowerCase().includes(q)) ||
    exp.summary.toLowerCase().includes(q)
  );

  if (results.length === 0) {
    console.log(color(`no results for: ${query}`, 'gray'));
    return;
  }

  console.log(color(`\n${results.length} result(s) for "${query}":`, 'cyan'));
  
  for (const exp of results) {
    console.log(`\n${color('━━━', 'gray')}`);
    console.log(`${color(exp.id, 'green')} - ${exp.title}`);
    console.log(color(`date: ${exp.date}`, 'gray'));
    if (exp.summary) console.log(color(exp.summary, 'gray'));
  }
}

// show exploration details
function showExploration(id: string): void {
  const index = getIndex();
  const exp = index.explorations.find(e => e.id === id);

  if (!exp) {
    console.log(color(`exploration not found: ${id}`, 'yellow'));
    return;
  }

  try {
    const content = readFileSync(exp.path, 'utf-8');
    const match = content.match(/---[\s\S]*?---([\s\S]*)/);
    const body = match ? match[1].trim() : content;

    console.log(`\n${color('━━━ ' + exp.title + ' ━━━', 'cyan')}`);
    console.log(color(`id: ${exp.id} | date: ${exp.date}`, 'gray'));
    if (exp.tags.length > 0) {
      console.log(color(`tags: ${exp.tags.join(', ')}`, 'gray'));
    }
    console.log();
    console.log(body);
  } catch (e) {
    console.log(color(`failed to read: ${(e as Error).message}`, 'yellow'));
  }
}

// update index (scan all markdown files in explorations dir)
function updateIndex(): void {
  const index = getIndex();
  let added = 0;
  let skipped = 0;

  try {
    if (!existsSync(EXPLORATIONS_DIR)) {
      console.log(color(`explorations directory not found: ${EXPLORATIONS_DIR}`, 'yellow'));
      return;
    }

    const files = readdirSync(EXPLORATIONS_DIR);
    
    for (const file of files) {
      if (!file.endsWith('.md')) continue;

      const path = join(EXPLORATIONS_DIR, file);
      const content = readFileSync(path, 'utf-8');
      const frontmatter = parseFrontmatter(content);

      if (!frontmatter?.id) continue;

      const exists = index.explorations.find(e => e.id === frontmatter.id);
      if (exists) {
        skipped++;
        continue;
      }

      index.explorations.push({
        id: frontmatter.id,
        path,
        title: frontmatter.title || file,
        date: frontmatter.date || new Date().toISOString().split('T')[0],
        tags: frontmatter.tags || [],
        summary: frontmatter.summary || '',
      });
      added++;
    }

    index.lastUpdated = new Date().toISOString();
    saveIndex(index);

    console.log(color(`index updated: +${added}, ${skipped} skipped`, 'green'));
    console.log(color(`total explorations: ${index.explorations.length}`, 'gray'));
  } catch (e) {
    console.log(color(`update failed: ${(e as Error).message}`, 'yellow'));
  }
}

// cli entry point
function main(): void {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command || command === 'help' || command === '--help' || command === '-h') {
    console.log(`
${color('mem', 'cyan')} - memory shortcuts and exploration browser

${color('Memory Shortcuts:', 'yellow')}
  mem recall [category]    show memory category
  mem recall               show all categories
  categories: ${Object.keys(MEMORY_PATHS).join(', ')}, all

${color('Exploration Browser:', 'yellow')}
  mem explore list         list all explorations
  mem explore search <q>   search explorations
  mem explore show <id>    show exploration details
  mem explore add <path>   add exploration to index
  mem explore update       rebuild index

${color('Examples:', 'gray')}
  mem recall soul
  mem recall goals
  mem explore list
  mem explore search "codex"
  mem explore show exp-001
`);
    return;
  }

  // handle recall commands
  if (command === 'recall') {
    const category = args[1] || 'all';
    showCategory(category);
    return;
  }

  // handle explore commands
  if (command === 'explore') {
    const subCommand = args[1];
    const query = args[2];

    switch (subCommand) {
      case 'list':
        listExplorations();
        break;
      case 'search':
        if (!query) {
          console.log(color('usage: mem explore search <query>', 'yellow'));
          return;
        }
        searchExplorations(query);
        break;
      case 'show':
        if (!query) {
          console.log(color('usage: mem explore show <id>', 'yellow'));
          return;
        }
        showExploration(query);
        break;
      case 'add':
        if (!query) {
          console.log(color('usage: mem explore add <path>', 'yellow'));
          return;
        }
        addExploration(query);
        break;
      case 'update':
        updateIndex();
        break;
      default:
        console.log(color(`unknown explore command: ${subCommand}`, 'yellow'));
        console.log(color('run "mem explore" for usage', 'gray'));
    }
    return;
  }

  console.log(color(`unknown command: ${command}`, 'yellow'));
  console.log(color('run "mem help" for usage', 'gray'));
}

main();

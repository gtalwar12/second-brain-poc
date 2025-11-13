# Proposal: Cross-Project Claude Memory System

**Author**: Claude (Sonnet 4.5)
**Date**: 2025-11-13
**Status**: Draft for Review
**Target**: ~/workspace/.claude/

---

## Executive Summary

This proposal outlines a **cross-project memory system** that enables Claude to maintain context, decisions, and state across all your projects and sessions. The system combines SQLite for queryable data with Markdown files for human-readable documentation, creating a persistent knowledge base that survives sessions and works across projects.

**Key Benefits**:
- ✅ Cross-project memory that persists indefinitely
- ✅ Queryable database for complex searches
- ✅ Human-readable Markdown files
- ✅ Automated session tracking
- ✅ Reusable code patterns and snippets
- ✅ Architectural decision records (ADRs)

---

## Problem Statement

Currently, Claude has no persistent memory across sessions. Each new conversation starts fresh, requiring:
- Re-explanation of project context
- Re-discovery of code locations
- Re-stating of architectural decisions
- Re-identification of known issues

This creates inefficiency and risks losing important context, especially across multiple projects.

---

## Proposed Solution

### Architecture Overview

A hybrid system combining:
1. **SQLite database** for structured, queryable facts
2. **Markdown files** for human-readable documentation
3. **Python helper library** for programmatic access
4. **Git integration** for version control

### Directory Structure

```
~/workspace/
├── .claude/                          # Cross-project Claude memory
│   ├── memory.db                     # SQLite database (queryable facts)
│   ├── GLOBAL_STATE.md               # Current state across all projects
│   ├── README.md                     # System documentation
│   ├── memory_helper.py              # Python CLI/library
│   ├── startup.sh                    # Auto-load on session start
│   │
│   ├── projects/                     # Per-project memory
│   │   ├── second-brain-poc.md
│   │   ├── ha-bridge.md
│   │   ├── substack-archive.md
│   │   └── [project-name].md
│   │
│   ├── sessions/                     # Session logs
│   │   ├── 2025-11/
│   │   │   ├── 2025-11-13.md
│   │   │   ├── 2025-11-14.md
│   │   │   └── ...
│   │   ├── 2025-12/
│   │   └── archive/                  # Old sessions (>6 months)
│   │
│   ├── decisions/                    # Architectural decisions
│   │   ├── INDEX.md                  # Decision index
│   │   ├── ADR-001-local-llm.md
│   │   ├── ADR-002-pm2-process-mgmt.md
│   │   └── ...
│   │
│   └── snippets/                     # Reusable code/config
│       ├── pm2-python-service.js
│       ├── applescript-reminders.sh
│       ├── flask-health-endpoint.py
│       └── ...
```

---

## Database Schema

### Core Tables

```sql
-- Projects table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    description TEXT,
    tech_stack TEXT,              -- JSON array: ["Python", "SQLite", ...]
    status TEXT DEFAULT 'active', -- 'active', 'paused', 'archived'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_active TEXT,
    UNIQUE(name)
);

-- Facts table (core memory storage)
CREATE TABLE facts (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    category TEXT NOT NULL,       -- 'config', 'decision', 'bug', 'fix', 'todo'
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    metadata TEXT,                -- JSON for extra context
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,              -- NULL = never expires
    superseded_by INTEGER,        -- Points to fact that replaces this
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (superseded_by) REFERENCES facts(id)
);

-- Code locations (important files/functions)
CREATE TABLE code_locations (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    description TEXT NOT NULL,
    tags TEXT,                    -- JSON array: ["pm2", "config", ...]
    last_verified TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Sessions (track work done)
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    session_date TEXT NOT NULL,
    project_id INTEGER,
    summary TEXT,
    tasks_completed INTEGER DEFAULT 0,
    duration_minutes INTEGER,
    notes TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Decisions (ADRs)
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    title TEXT NOT NULL,
    context TEXT,
    decision TEXT NOT NULL,
    alternatives TEXT,            -- JSON array
    consequences TEXT,
    status TEXT DEFAULT 'accepted', -- 'proposed', 'accepted', 'deprecated', 'superseded'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    superseded_by INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (superseded_by) REFERENCES decisions(id)
);

-- Cross-project patterns (reusable solutions)
CREATE TABLE cross_project_patterns (
    id INTEGER PRIMARY KEY,
    pattern_name TEXT UNIQUE NOT NULL,
    description TEXT,
    used_in_projects TEXT,        -- JSON array of project IDs
    code_snippet TEXT,
    language TEXT,
    tags TEXT,                    -- JSON array
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_facts_project ON facts(project_id);
CREATE INDEX idx_facts_category ON facts(category);
CREATE INDEX idx_facts_created ON facts(created_at);
CREATE INDEX idx_code_locations_project ON code_locations(project_id);
CREATE INDEX idx_code_locations_tags ON code_locations(tags);
CREATE INDEX idx_sessions_date ON sessions(session_date);
CREATE INDEX idx_sessions_project ON sessions(project_id);
CREATE INDEX idx_decisions_project ON decisions(project_id);
CREATE INDEX idx_decisions_status ON decisions(status);
```

---

## Markdown File Templates

### 1. GLOBAL_STATE.md

```markdown
# Global Claude Memory

**Last Update**: 2025-11-13 09:50 PST
**Active Projects**: 3

---

## Currently Active Projects

### second-brain-poc
- **Status**: Active development
- **Tech**: Python 3.14, Qwen 2.5 7B, SQLite, Apple Integrations
- **Last session**: 2025-11-13
- **Quick start**: `pm2 status second-brain`
- **Port**: 8898

### ha-bridge
- **Status**: Running in production
- **Tech**: Python, Home Assistant API, Flask
- **Last session**: 2025-11-10
- **Quick start**: `pm2 status ha-bridge`
- **Port**: 8899

### substack-archive
- **Status**: Paused
- **Tech**: Python, OpenRouter API
- **Last session**: 2025-10-15

---

## Global Environment

### System Info
- **OS**: macOS (Darwin 25.1.0)
- **User**: home-mini
- **Workspace**: ~/workspace/

### Tools & Versions
- **Python**: 3.14 (Homebrew)
- **Node**: v22.20.0 (nvm)
- **Package managers**: Homebrew, npm, pip
- **Process manager**: PM2 v6.0.13

### API Keys & Services
- **OpenRouter API**: ~/.env (OPENROUTER_API_KEY)
- **Home Assistant**: http://192.168.10.125:8123
- **Ollama**: http://localhost:11434

### Global Preferences
- **Default LLM**: OpenRouter (Claude 3.5 Sonnet)
- **Communication style**: Concise, technical, no emojis
- **Code style**: Black (Python), Prettier (JS)

---

## Common Paths

| Path | Description |
|------|-------------|
| `~/workspace/` | All projects |
| `~/.claude/` | Claude memory system |
| `~/ha-config/` | Home Assistant config (SMB mount) |
| `~/.config/` | Application configs |
| `~/scripts/` | Utility scripts |

---

## Cross-Project Patterns

### PM2 Python Service
- **Used in**: second-brain-poc, ha-bridge, tts-ingest
- **Pattern**: ecosystem.config.js with Python interpreter
- **Snippet**: `~/.claude/snippets/pm2-python-service.js`

### Flask Health Endpoint
- **Used in**: second-brain-poc, ha-bridge, orchestrator-api
- **Pattern**: `/health` endpoint returning JSON status
- **Snippet**: `~/.claude/snippets/flask-health-endpoint.py`

### SQLite Knowledge Graph
- **Used in**: second-brain-poc
- **Pattern**: Nodes + Edges tables with JSON properties
- **Snippet**: `~/.claude/snippets/sqlite-kg-schema.sql`
```

### 2. projects/[project-name].md

```markdown
# {Project Name} - Memory

**Path**: ~/workspace/{project-name}
**Status**: Active | Paused | Archived
**Tech Stack**: Python, SQLite, Flask, PM2
**Last Active**: 2025-11-13
**Repository**: https://github.com/username/project-name

---

## Quick Reference

### Services
| Service | Status | Port | Command |
|---------|--------|------|---------|
| PM2: second-brain | Running | 8898 | `pm2 status second-brain` |
| Ollama | Running | 11434 | `curl http://localhost:11434/api/tags` |

### Key Commands
```bash
# Start service
pm2 start second-brain

# View logs
pm2 logs second-brain --lines 50

# Health check
curl http://localhost:8898/health

# Test endpoint
curl -X POST http://localhost:8898/capture/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## Current State

### Configuration
- **Port**: 8898
- **Polling interval**: 10 seconds
- **Python venv**: ./venv/bin/python3
- **Model**: qwen2.5:7b-instruct (Ollama)

### Important Files
| File | Lines | Description |
|------|-------|-------------|
| `orchestrator.py` | 47, 294 | Main entry point, 10s polling |
| `action_handlers.py` | 138 | Checkbox format fix |
| `brain_client.py` | 25 | Qwen model interface |
| `prompts/brain_system_prompt.md` | - | Model instructions |
| `ecosystem.config.js` | - | PM2 configuration |

### Dependencies
- **Ollama**: qwen2.5:7b-instruct model
- **Python packages**: See requirements.txt
- **System requirements**: macOS with AppleScript support

---

## Recent Changes

### 2025-11-13 (Today)
- ✅ Setup PM2 service management
- ✅ Reduced polling interval from 20s to 10s
- ✅ Fixed checkbox display format (removed ul/li wrappers)
- ✅ Created PM2 ecosystem.config.js
- ✅ Verified auto-start on boot
- ✅ Designed cross-project memory system

### 2025-11-12
- ✅ Implemented URL capture endpoint
- ✅ Fixed AppleScript parser for reminders
- ✅ Created system prompt externalization

---

## Known Issues

| Issue | Location | Severity | Status | Notes |
|-------|----------|----------|--------|-------|
| Recipe URL wrong schema | Model output | Medium | Open | Returns `kg_response` instead of `graph_updates` |
| Reminder deletion fails | AppleScript | Low | Known limitation | Delete command not working |
| Checkbox display | Fixed | - | Resolved | Changed to `<div><en-todo/>` format |

---

## Architecture Decisions

### ADR-001: Use Local LLM (Qwen 2.5 7B)
- **Context**: Need offline-capable AI brain
- **Decision**: Use Qwen 2.5 7B via Ollama
- **Alternatives**: Cloud API (OpenRouter, OpenAI)
- **Reason**: Privacy, cost, offline capability
- **Status**: Accepted

### ADR-002: PM2 for Process Management
- **Context**: Need persistent service for orchestrator
- **Decision**: Use PM2 with ecosystem.config.js
- **Alternatives**: systemd, launchd, supervisord
- **Reason**: Already using PM2 for other services, familiar tooling
- **Status**: Accepted

---

## Next Steps

- [ ] Fix recipe URL schema output
- [ ] Test checkbox display on iPhone
- [ ] Add recipe storage to knowledge graph
- [ ] Implement recipe-to-grocery extraction
- [ ] Commit recent changes to GitHub

---

## Notes

### Grocery Categories (13)
1. Produce
2. Meat & Seafood
3. Dairy & Eggs
4. Bakery & Bread
5. Pantry & Dry Goods
6. Canned & Jarred Goods
7. Frozen Foods
8. Snacks & Sweets
9. Beverages
10. Condiments & Sauces
11. Spices & Seasonings
12. Health & Personal Care
13. Household & Cleaning

### Model Behavior
- **Mode**: Capture (store_only)
- **Channels**: reminder, apple_note, url_text, chat
- **Output format**: JSON with graph_updates and actions
- **Item canonicalization**: Singular form, lowercase
```

### 3. sessions/YYYY-MM/YYYY-MM-DD.md

```markdown
# Session: 2025-11-13

**Projects Worked On**: second-brain-poc
**Duration**: ~2 hours
**Focus**: PM2 setup, memory system design
**Claude Model**: Sonnet 4.5

---

## Summary

Setup PM2 for persistent service management, reduced polling interval to 10 seconds, fixed checkbox display format, and designed comprehensive cross-project memory system.

---

## Tasks Completed

### second-brain-poc

1. ✅ **Setup PM2 service management**
   - Created ecosystem.config.js
   - Configured auto-restart and logging
   - Verified boot startup via LaunchAgent

2. ✅ **Reduced polling interval**
   - Changed from 20s to 10s in orchestrator.py
   - Updated default parameter and main() call

3. ✅ **Fixed checkbox display format**
   - Modified action_handlers.py:138
   - Changed from `<ul><li>` wrapper to direct `<div><en-todo/>`
   - Restarted service with fix

4. ✅ **Created PM2_SETUP.md documentation**
   - Documented all PM2 commands
   - Added troubleshooting guide
   - Included health check examples

5. ✅ **Designed cross-project memory system**
   - Created database schema
   - Designed directory structure
   - Wrote proposal document

---

## Decisions Made

### ADR-002: Use PM2 for Process Management

**Context**: The orchestrator needs to run persistently and survive system reboots.

**Decision**: Use PM2 with ecosystem.config.js for process management.

**Alternatives Considered**:
- systemd (Linux-only)
- launchd (complex plist configuration)
- supervisord (additional dependency)
- Custom bash script with nohup

**Rationale**:
- Already using PM2 for other services (ha-bridge, audiobookshelf, etc.)
- Familiar tooling and commands
- Built-in logging and auto-restart
- Cross-platform (works on macOS and Linux)
- Easy integration with existing workflow

**Consequences**:
- ✅ Unified process management across all services
- ✅ Simple log viewing with `pm2 logs`
- ✅ Easy to add more services in the future
- ⚠️ Dependency on npm/node ecosystem
- ⚠️ Requires PM2 to be running

**Status**: Accepted

---

## Code Changes

| File | Lines Changed | Description |
|------|---------------|-------------|
| `orchestrator.py` | 47, 294 | Changed default poll_interval from 20 to 10 |
| `action_handlers.py` | 135-139 | Removed ul/li wrapper, use direct div/en-todo |
| `ecosystem.config.js` | New file | PM2 configuration for second-brain service |
| `PM2_SETUP.md` | New file | Documentation for PM2 setup and usage |
| `CLAUDE_MEMORY_PROPOSAL.md` | New file | Proposal for cross-project memory system |

---

## Issues Found

### Issue #1: Recipe URL Processing Wrong Schema

**Description**: When processing recipe URLs, the model returns `kg_response.grocery_items_to_add` instead of following the required `graph_updates` and `actions` schema.

**Impact**: Grocery items from recipes are not added to the note.

**Example**:
```json
{
  "kg_response": {
    "grocery_items_to_add": [...]
  },
  "recipe_steps": [...],
  "graph_updates": [],
  "actions": []
}
```

**Expected**:
```json
{
  "graph_updates": [
    {"op_type": "create_node", "payload": {...}}
  ],
  "actions": [
    {"action_type": "update_apple_note", "arguments": {...}}
  ]
}
```

**Root Cause**: System prompt may not be strict enough about output format for url_text channel.

**Status**: Open
**Priority**: Medium
**Next Steps**: Review and strengthen system prompt for URL processing

---

## Learnings

### PM2 Configuration
- Python scripts need explicit interpreter path in ecosystem.config.js
- Use `PYTHONUNBUFFERED=1` env var for real-time log output
- `pm2 save` is required to persist process list across reboots
- LaunchAgent setup only needed once per system

### Apple Notes HTML Format
- `<en-todo/>` creates checkboxes in Apple Notes
- Must NOT wrap in `<ul><li>` tags (creates bullets instead)
- Correct format: `<div><en-todo/>Item text</div>`

### AppleScript Parsing
- AppleScript returns comma-separated values, not JSON
- Simple string split works better than complex parsing
- Missing values return "missing value" string

---

## Metrics

- **Interactions processed**: 9 total
- **Service uptime**: 34 seconds (after restart)
- **Memory usage**: ~47MB
- **CPU usage**: <1% idle, ~10-20% during processing

---

## Next Session Prep

### Immediate Tasks
1. Fix recipe URL schema output
2. Test checkbox display on iPhone with new reminder
3. Commit recent changes to GitHub

### Future Enhancements
1. Implement cross-project memory system
2. Add recipe storage to knowledge graph
3. Create web UI for viewing grocery list
4. Add ingredient quantity tracking

---

## Context for Next Session

**Last command run**:
```bash
pm2 status second-brain
```

**Service status**: Running (PID 51367, port 8898)

**Recent file edits**:
- orchestrator.py (polling interval)
- action_handlers.py (checkbox format)
- ecosystem.config.js (created)

**Waiting on**: User to test checkbox display on iPhone
```

### 4. decisions/ADR-XXX-title.md (Architecture Decision Record)

```markdown
# ADR-002: Use PM2 for Process Management

**Status**: Accepted
**Date**: 2025-11-13
**Deciders**: User, Claude
**Project**: second-brain-poc (also applies to other services)

---

## Context

The Second Brain orchestrator needs to:
- Run persistently as a background service
- Automatically restart on crashes
- Start automatically after system reboot
- Provide easy access to logs
- Monitor resource usage

Currently running the orchestrator manually via:
```bash
python3 orchestrator.py
```

This requires keeping a terminal open and doesn't survive reboots.

---

## Decision

Use **PM2 (Process Manager 2)** with an ecosystem.config.js configuration file to manage the orchestrator service.

Configuration:
```javascript
module.exports = {
  apps: [{
    name: 'second-brain',
    script: 'orchestrator.py',
    interpreter: './venv/bin/python3',
    instances: 1,
    autorestart: true,
    max_memory_restart: '500M',
    // ... see ecosystem.config.js for full config
  }]
};
```

---

## Alternatives Considered

### 1. systemd
**Pros**:
- Native Linux service manager
- Robust and well-tested
- Integrated with system logging

**Cons**:
- Linux-only (not available on macOS)
- More complex configuration
- Requires sudo for installation

### 2. launchd (macOS)
**Pros**:
- Native macOS service manager
- Integrated with system

**Cons**:
- Complex plist XML configuration
- Difficult to debug
- macOS-only

### 3. supervisord
**Pros**:
- Cross-platform
- Python-based
- Good web UI

**Cons**:
- Additional dependency to install
- Less familiar tooling
- Separate config format to learn

### 4. Custom bash script with nohup
**Pros**:
- No dependencies
- Simple

**Cons**:
- No auto-restart on crash
- No log management
- Manual startup required
- Poor monitoring capabilities

---

## Rationale

PM2 was selected because:

1. **Already in use**: We're already using PM2 for other services:
   - audiobookshelf
   - cloudflare-tunnel
   - ha-bridge
   - orchestrator-api
   - tts-ingest
   - verify-server
   - whenmoon
   - www-server

2. **Familiar tooling**: Team already knows PM2 commands and workflows

3. **Excellent logging**: Built-in log management with rotation
   ```bash
   pm2 logs second-brain
   pm2 logs second-brain --lines 100
   ```

4. **Auto-restart**: Automatically restarts on crashes with configurable limits

5. **Boot startup**: Easy boot integration via LaunchAgent (already configured)
   ```bash
   pm2 save
   ```

6. **Resource monitoring**: Built-in monitoring
   ```bash
   pm2 monit
   pm2 status
   ```

7. **Cross-platform**: Works on both macOS (current) and Linux (future)

---

## Consequences

### Positive

- ✅ Unified process management across all services
- ✅ Simple log viewing and monitoring
- ✅ Reliable auto-restart on failures
- ✅ Easy to add more Python services in the future
- ✅ Familiar tooling reduces onboarding time
- ✅ Good ecosystem integration (PM2 Plus for advanced monitoring)

### Negative

- ⚠️ Dependency on npm/node ecosystem (but already using it)
- ⚠️ PM2 daemon must be running (but already is)
- ⚠️ Additional config file to maintain (ecosystem.config.js)
- ⚠️ Memory overhead of PM2 daemon (~50MB, but shared across all services)

### Neutral

- 📝 Need to document PM2 commands for team
- 📝 Need to ensure PM2 is installed on new systems
- 📝 Log files accumulate over time (need rotation strategy)

---

## Implementation

1. Create ecosystem.config.js with service configuration
2. Stop any running orchestrator processes
3. Start service: `pm2 start ecosystem.config.js`
4. Save process list: `pm2 save`
5. Verify auto-start: LaunchAgent already exists at `~/Library/LaunchAgents/pm2.home-mini.plist`

---

## Compliance

This decision follows the project's principles:
- ✅ Use existing tools when possible
- ✅ Minimize dependencies
- ✅ Prefer battle-tested solutions
- ✅ Keep configuration simple and documented

---

## Related Decisions

- ADR-001: Use Local LLM (Qwen 2.5 7B via Ollama)
- Future: ADR-003: Service discovery and health monitoring

---

## Notes

- PM2 version: 6.0.13
- Node version: v22.20.0 (via nvm)
- Python version: 3.14
- macOS version: Darwin 25.1.0

---

## References

- PM2 Documentation: https://pm2.keymetrics.io/docs/usage/quick-start/
- ecosystem.config.js: ~/workspace/second-brain-poc/ecosystem.config.js
- PM2_SETUP.md: ~/workspace/second-brain-poc/PM2_SETUP.md
```

---

## Python Helper Library

### memory_helper.py

```python
#!/usr/bin/env python3
"""
Claude Memory Helper
Programmatic interface to cross-project memory system

Usage:
    # CLI
    ./memory_helper.py add --project second-brain-poc --category config --key port --value 8898
    ./memory_helper.py get --project second-brain-poc
    ./memory_helper.py search --query "PM2"
    ./memory_helper.py session --project second-brain-poc --summary "Fixed bugs" --tasks 5

    # Python API
    from memory_helper import ClaudeMemory
    mem = ClaudeMemory()
    mem.add_fact("second-brain-poc", "config", "port", "8898")
    state = mem.get_project_state("second-brain-poc")
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ClaudeMemory:
    """Interface to Claude's cross-project memory system"""

    def __init__(self, db_path: str = "~/workspace/.claude/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Initialize database schema if not exists"""
        cursor = self.conn.cursor()

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                path TEXT NOT NULL,
                description TEXT,
                tech_stack TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT
            )
        """)

        # Facts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                superseded_by INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (superseded_by) REFERENCES facts(id)
            )
        """)

        # Code locations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_locations (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                line_start INTEGER,
                line_end INTEGER,
                description TEXT NOT NULL,
                tags TEXT,
                last_verified TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                session_date TEXT NOT NULL,
                project_id INTEGER,
                summary TEXT,
                tasks_completed INTEGER DEFAULT 0,
                duration_minutes INTEGER,
                notes TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY,
                project_id INTEGER,
                title TEXT NOT NULL,
                context TEXT,
                decision TEXT NOT NULL,
                alternatives TEXT,
                consequences TEXT,
                status TEXT DEFAULT 'accepted',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                superseded_by INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (superseded_by) REFERENCES decisions(id)
            )
        """)

        # Cross-project patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cross_project_patterns (
                id INTEGER PRIMARY KEY,
                pattern_name TEXT UNIQUE NOT NULL,
                description TEXT,
                used_in_projects TEXT,
                code_snippet TEXT,
                language TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_project ON facts(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_code_locations_project ON code_locations(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project_id)")

        self.conn.commit()

    def _get_project_id(self, project_name: str) -> Optional[int]:
        """Get project ID by name, create if doesn't exist"""
        cursor = self.conn.cursor()
        result = cursor.execute(
            "SELECT id FROM projects WHERE name = ?",
            (project_name,)
        ).fetchone()

        if result:
            return result['id']

        # Create project if doesn't exist
        project_path = f"~/workspace/{project_name}"
        cursor.execute(
            "INSERT INTO projects (name, path, last_active) VALUES (?, ?, ?)",
            (project_name, project_path, datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_fact(self, project: str, category: str, key: str, value: str,
                 metadata: Optional[Dict] = None, expires_at: Optional[str] = None):
        """Add a fact to the memory system"""
        project_id = self._get_project_id(project)
        cursor = self.conn.cursor()

        metadata_json = json.dumps(metadata) if metadata else None

        cursor.execute("""
            INSERT INTO facts (project_id, category, key, value, metadata, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, category, key, value, metadata_json, expires_at))

        self.conn.commit()
        return cursor.lastrowid

    def get_project_state(self, project: str) -> Dict:
        """Get current state of a project"""
        project_id = self._get_project_id(project)
        cursor = self.conn.cursor()

        # Get project info
        project_info = cursor.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()

        # Get all non-expired facts
        facts = cursor.execute("""
            SELECT category, key, value, created_at
            FROM facts
            WHERE project_id = ?
              AND (expires_at IS NULL OR expires_at > ?)
              AND superseded_by IS NULL
            ORDER BY created_at DESC
        """, (project_id, datetime.now(timezone.utc).isoformat())).fetchall()

        # Get code locations
        code_locations = cursor.execute("""
            SELECT file_path, line_start, line_end, description, tags
            FROM code_locations
            WHERE project_id = ?
            ORDER BY file_path
        """, (project_id,)).fetchall()

        # Get recent sessions
        sessions = cursor.execute("""
            SELECT session_date, summary, tasks_completed
            FROM sessions
            WHERE project_id = ?
            ORDER BY session_date DESC
            LIMIT 5
        """, (project_id,)).fetchall()

        return {
            'project': dict(project_info) if project_info else {},
            'facts': [dict(f) for f in facts],
            'code_locations': [dict(c) for c in code_locations],
            'recent_sessions': [dict(s) for s in sessions]
        }

    def search_facts(self, query: str, project: Optional[str] = None,
                    category: Optional[str] = None) -> List[Dict]:
        """Search facts across projects"""
        cursor = self.conn.cursor()

        sql = """
            SELECT f.*, p.name as project_name
            FROM facts f
            JOIN projects p ON f.project_id = p.id
            WHERE (f.key LIKE ? OR f.value LIKE ?)
              AND (f.expires_at IS NULL OR f.expires_at > ?)
              AND f.superseded_by IS NULL
        """
        params = [f"%{query}%", f"%{query}%", datetime.now(timezone.utc).isoformat()]

        if project:
            sql += " AND p.name = ?"
            params.append(project)

        if category:
            sql += " AND f.category = ?"
            params.append(category)

        sql += " ORDER BY f.created_at DESC LIMIT 50"

        results = cursor.execute(sql, params).fetchall()
        return [dict(r) for r in results]

    def record_session(self, project: str, summary: str,
                      tasks_completed: int = 0, duration_minutes: Optional[int] = None,
                      notes: Optional[str] = None):
        """Record a session"""
        project_id = self._get_project_id(project)
        cursor = self.conn.cursor()

        session_date = datetime.now(timezone.utc).date().isoformat()

        cursor.execute("""
            INSERT INTO sessions (session_date, project_id, summary, tasks_completed, duration_minutes, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_date, project_id, summary, tasks_completed, duration_minutes, notes))

        # Update project last_active
        cursor.execute(
            "UPDATE projects SET last_active = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), project_id)
        )

        self.conn.commit()
        return cursor.lastrowid

    def add_code_location(self, project: str, file_path: str, description: str,
                         line_start: Optional[int] = None, line_end: Optional[int] = None,
                         tags: Optional[List[str]] = None):
        """Add a code location"""
        project_id = self._get_project_id(project)
        cursor = self.conn.cursor()

        tags_json = json.dumps(tags) if tags else None

        cursor.execute("""
            INSERT INTO code_locations (project_id, file_path, line_start, line_end, description, tags, last_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_id, file_path, line_start, line_end, description, tags_json,
              datetime.now(timezone.utc).isoformat()))

        self.conn.commit()
        return cursor.lastrowid

    def find_code(self, description: str, project: Optional[str] = None) -> List[Dict]:
        """Find code by description"""
        cursor = self.conn.cursor()

        sql = """
            SELECT c.*, p.name as project_name
            FROM code_locations c
            JOIN projects p ON c.project_id = p.id
            WHERE c.description LIKE ?
        """
        params = [f"%{description}%"]

        if project:
            sql += " AND p.name = ?"
            params.append(project)

        sql += " ORDER BY c.last_verified DESC"

        results = cursor.execute(sql, params).fetchall()
        return [dict(r) for r in results]

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Memory CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a fact')
    add_parser.add_argument('--project', required=True)
    add_parser.add_argument('--category', required=True,
                           choices=['config', 'decision', 'bug', 'fix', 'todo'])
    add_parser.add_argument('--key', required=True)
    add_parser.add_argument('--value', required=True)

    # Get command
    get_parser = subparsers.add_parser('get', help='Get project state')
    get_parser.add_argument('--project', required=True)

    # Search command
    search_parser = subparsers.add_parser('search', help='Search facts')
    search_parser.add_argument('--query', required=True)
    search_parser.add_argument('--project')
    search_parser.add_argument('--category')

    # Session command
    session_parser = subparsers.add_parser('session', help='Record a session')
    session_parser.add_argument('--project', required=True)
    session_parser.add_argument('--summary', required=True)
    session_parser.add_argument('--tasks', type=int, default=0)
    session_parser.add_argument('--duration', type=int)

    # Code command
    code_parser = subparsers.add_parser('code', help='Add code location')
    code_parser.add_argument('--project', required=True)
    code_parser.add_argument('--file', required=True)
    code_parser.add_argument('--description', required=True)
    code_parser.add_argument('--line-start', type=int)
    code_parser.add_argument('--line-end', type=int)
    code_parser.add_argument('--tags', nargs='*')

    args = parser.parse_args()

    mem = ClaudeMemory()

    try:
        if args.command == 'add':
            fact_id = mem.add_fact(args.project, args.category, args.key, args.value)
            print(f"✓ Added fact #{fact_id}: {args.key} = {args.value}")

        elif args.command == 'get':
            state = mem.get_project_state(args.project)
            print(json.dumps(state, indent=2))

        elif args.command == 'search':
            results = mem.search_facts(args.query, args.project, args.category)
            print(f"Found {len(results)} results:")
            for r in results:
                print(f"  [{r['project_name']}] {r['category']}: {r['key']} = {r['value']}")

        elif args.command == 'session':
            session_id = mem.record_session(
                args.project, args.summary, args.tasks, args.duration
            )
            print(f"✓ Recorded session #{session_id}")

        elif args.command == 'code':
            code_id = mem.add_code_location(
                args.project, args.file, args.description,
                args.line_start, args.line_end, args.tags
            )
            print(f"✓ Added code location #{code_id}")

        else:
            parser.print_help()

    finally:
        mem.close()


if __name__ == "__main__":
    main()
```

---

## Implementation Plan

### Phase 1: Setup (15 minutes)

**Tasks**:
1. Create directory structure at `~/workspace/.claude/`
2. Initialize SQLite database with schema
3. Create `GLOBAL_STATE.md` template
4. Create `README.md` with system documentation

**Commands**:
```bash
# Create directories
mkdir -p ~/workspace/.claude/{projects,sessions/2025-11,decisions,snippets}

# Initialize database
cd ~/workspace/.claude
python3 memory_helper.py  # Will auto-create schema

# Create global state
cat > GLOBAL_STATE.md << 'EOF'
[template content]
EOF
```

### Phase 2: Helper Script (30 minutes)

**Tasks**:
1. Write `memory_helper.py` with core functions
2. Test database operations
3. Add CLI interface
4. Make executable

**Commands**:
```bash
chmod +x ~/workspace/.claude/memory_helper.py

# Test
./memory_helper.py add --project test --category config --key test --value "works"
./memory_helper.py get --project test
```

### Phase 3: Initial Population (30 minutes)

**Tasks**:
1. Create `projects/second-brain-poc.md` with current state
2. Record today's session in `sessions/2025-11/2025-11-13.md`
3. Create ADR-002 for PM2 decision
4. Add current facts to database

**Commands**:
```bash
# Add facts
./memory_helper.py add --project second-brain-poc --category config --key port --value 8898
./memory_helper.py add --project second-brain-poc --category config --key polling_interval --value 10
./memory_helper.py add --project second-brain-poc --category bug --key recipe_url_schema --value "Returns kg_response instead of graph_updates"

# Add code locations
./memory_helper.py code --project second-brain-poc --file orchestrator.py --description "Main entry point, 10s polling" --line-start 294 --tags pm2 config

# Record session
./memory_helper.py session --project second-brain-poc --summary "Setup PM2, reduced polling to 10s, fixed checkboxes" --tasks 7 --duration 120
```

### Phase 4: Integration (15 minutes)

**Tasks**:
1. Add startup hook to `~/.zshrc` (optional)
2. Create `startup.sh` script
3. Test memory recall

**Commands**:
```bash
# Add to ~/.zshrc (optional)
echo 'alias claude-memory="~/workspace/.claude/memory_helper.py"' >> ~/.zshrc

# Test recall
./memory_helper.py get --project second-brain-poc
./memory_helper.py search --query "PM2"
```

---

## Usage Examples

### Example 1: Starting a New Session

```bash
# View global state
cat ~/workspace/.claude/GLOBAL_STATE.md

# View project state
~/workspace/.claude/memory_helper.py get --project second-brain-poc | jq .

# Check recent sessions
ls -lt ~/workspace/.claude/sessions/2025-11/
```

### Example 2: Recording Work

```bash
# Add a fact
./memory_helper.py add \
  --project second-brain-poc \
  --category fix \
  --key checkbox_display \
  --value "Changed to <div><en-todo/> format"

# Add code location
./memory_helper.py code \
  --project second-brain-poc \
  --file action_handlers.py \
  --description "Checkbox format fix" \
  --line-start 135 \
  --line-end 139 \
  --tags fix checkbox apple-notes

# Record session
./memory_helper.py session \
  --project second-brain-poc \
  --summary "Fixed checkbox display bug" \
  --tasks 1 \
  --duration 30
```

### Example 3: Finding Information

```bash
# Search for PM2-related facts
./memory_helper.py search --query "PM2"

# Search within a project
./memory_helper.py search --query "port" --project second-brain-poc

# Find code by description
./memory_helper.py find --description "checkbox"

# Direct SQL query
sqlite3 ~/workspace/.claude/memory.db \
  "SELECT * FROM facts WHERE category='bug' AND superseded_by IS NULL"
```

### Example 4: Cross-Project Patterns

```bash
# Search for PM2 usage across all projects
./memory_helper.py search --query "ecosystem.config.js"

# View snippet
cat ~/workspace/.claude/snippets/pm2-python-service.js
```

---

## Benefits Analysis

### Time Savings

**Current state** (no memory):
- 5-10 minutes explaining project context each session
- 2-5 minutes re-discovering code locations
- 3-5 minutes remembering recent decisions
- **Total: 10-20 minutes per session**

**With memory system**:
- 1 minute reading GLOBAL_STATE.md
- Instant access to project facts
- Searchable decision history
- **Total: 1-2 minutes per session**

**Savings**: 8-18 minutes per session = **40-90 minutes per week**

### Context Quality

**Without memory**:
- ❌ May forget important decisions
- ❌ May suggest already-tried solutions
- ❌ Limited awareness of cross-project patterns
- ❌ No history of what worked/didn't work

**With memory**:
- ✅ Full context of all decisions and reasoning
- ✅ Knowledge of past attempts and outcomes
- ✅ Cross-project learning and patterns
- ✅ Searchable history of all work

### Development Velocity

**Scenarios enabled**:
1. "What port is service X running on?" → Instant answer from facts
2. "Where did we fix the checkbox bug?" → Code location query
3. "Why did we choose PM2?" → ADR lookup
4. "What other projects use Flask?" → Cross-project search
5. "What did we work on last session?" → Session history

---

## Maintenance

### Daily
- Auto-update `GLOBAL_STATE.md` timestamp via startup.sh
- Record session summary at end of work

### Weekly
- Review and update project markdown files
- Archive old session files (>30 days)
- Backup database

### Monthly
- Clean up expired facts
- Update cross-project patterns
- Review and close completed todos

### Commands

```bash
# Backup database
cp ~/workspace/.claude/memory.db ~/workspace/.claude/memory.db.backup-$(date +%Y%m%d)

# Archive old sessions
mv ~/workspace/.claude/sessions/2025-10/* ~/workspace/.claude/sessions/archive/

# Clean expired facts
sqlite3 ~/workspace/.claude/memory.db \
  "DELETE FROM facts WHERE expires_at < datetime('now')"
```

---

## Security & Privacy

### Data Stored
- Project names and paths
- Configuration values (ports, settings)
- Code locations and descriptions
- Session summaries
- Decision rationale

### NOT Stored
- API keys or secrets
- Personal information
- Proprietary code (only descriptions)
- Passwords or credentials

### Best Practices
1. Never add secrets to facts
2. Use generic descriptions for sensitive code
3. Keep database file local (don't sync to cloud)
4. Regular backups to encrypted storage
5. Git-ignore the database file

---

## Future Enhancements

### Short-term (1-3 months)
- [ ] Web UI for browsing memory
- [ ] Auto-detect project changes and update facts
- [ ] Integration with git hooks for automatic session recording
- [ ] Slack/Discord bot interface

### Medium-term (3-6 months)
- [ ] AI-powered fact extraction from code
- [ ] Automatic ADR generation from git commits
- [ ] Cross-project dependency tracking
- [ ] Performance metrics and analytics

### Long-term (6-12 months)
- [ ] Multi-user support for team collaboration
- [ ] Integration with external tools (JIRA, Linear, etc.)
- [ ] Advanced search with semantic similarity
- [ ] Predictive suggestions based on patterns

---

## Conclusion

The proposed cross-project memory system provides a robust, scalable solution for maintaining context across all your projects and sessions with Claude. By combining the queryability of SQLite with the readability of Markdown, the system offers both human and machine-friendly interfaces.

**Implementation effort**: ~90 minutes
**Ongoing maintenance**: ~5 minutes per session
**Time savings**: 8-18 minutes per session
**ROI**: Positive after ~10 sessions (~2 weeks)

---

## Next Steps

**For approval**:
1. Review this proposal
2. Approve or request changes
3. Schedule implementation (estimated 90 minutes)

**For implementation**:
1. Phase 1: Setup directory structure and database (15 min)
2. Phase 2: Implement Python helper (30 min)
3. Phase 3: Populate with current state (30 min)
4. Phase 4: Integration and testing (15 min)

---

## Appendix: File Locations

| File | Location |
|------|----------|
| This proposal | `~/workspace/CLAUDE_MEMORY_PROPOSAL.md` |
| Database | `~/workspace/.claude/memory.db` |
| Helper script | `~/workspace/.claude/memory_helper.py` |
| Global state | `~/workspace/.claude/GLOBAL_STATE.md` |
| Project memories | `~/workspace/.claude/projects/*.md` |
| Session logs | `~/workspace/.claude/sessions/YYYY-MM/*.md` |
| Decisions | `~/workspace/.claude/decisions/ADR-*.md` |
| Snippets | `~/workspace/.claude/snippets/*` |

---

**END OF PROPOSAL**

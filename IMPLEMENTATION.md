# Second Brain PoC - Implementation Summary

## Overview

This is a working proof-of-concept implementation of a "Second Brain" system that:
- Uses a **local Qwen 2.5 7B-8B instruct model** (via Ollama) as the reasoning engine
- Accepts inputs from **Apple Reminders**, **Apple Notes**, and **web URLs**
- Maintains a **SQLite knowledge graph** of grocery items and relationships
- Outputs a single **"Groceries" note** in Apple Notes with categorized checklists
- Logs all interactions for future training

## Implementation Status: ✅ COMPLETE

All components have been implemented and tested:

1. ✅ Local brain model (Qwen 2.5 7B-8B via Ollama)
2. ✅ Knowledge graph database (SQLite)
3. ✅ Brain client with structured JSON output
4. ✅ Apple Reminders integration (list, read, delete)
5. ✅ Apple Notes integration (list, read, create/update with checklists)
6. ✅ Action handlers (update note, delete reminder)
7. ✅ Orchestrator service (polling + HTTP endpoint)
8. ✅ URL capture endpoint with web scraping
9. ✅ Interaction logging to JSONL

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                           │
│                    (orchestrator.py)                        │
│                                                             │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  Event Watchers │  │  HTTP Server │  │  Action Exec  │ │
│  │  (poll)         │  │  (Flask)     │  │               │ │
│  └─────────────────┘  └──────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Reminders   │     │   URL Fetch  │     │  Notes API   │
│  (osascript) │     │  (requests)  │     │  (osascript) │
└──────────────┘     └──────────────┘     └──────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │  Brain Client│
                      │   (Ollama)   │
                      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │ Knowledge    │
                      │ Graph (SQLite)│
                      └──────────────┘
```

## Files and Responsibilities

### Core Engine
- **orchestrator.py** (280 lines)
  - Main service loop
  - Polls Reminders/Notes every 20s
  - HTTP server for URL capture (port 8899)
  - Coordinates all components
  - Entry point: `python3 orchestrator.py`

### AI/LLM Layer
- **brain_client.py** (140 lines)
  - Interface to local Qwen 2.5 7B-8B via Ollama
  - System prompt with grocery domain knowledge
  - Structured JSON output enforcement
  - Handles model communication

### Data Layer
- **kg_database.py** (220 lines)
  - SQLite-based knowledge graph
  - Tables: `nodes`, `edges`
  - Operations: create_node, update_node, create_edge
  - Graph update interpreter for model outputs

### Integration Layer
- **apple_integrations.py** (230 lines)
  - `RemindersIntegration`: list, delete reminders via osascript
  - `NotesIntegration`: list, create/update notes via osascript
  - AppleScript parsing and execution

### Execution Layer
- **action_handlers.py** (140 lines)
  - `ActionExecutor`: executes model-returned actions
  - `update_apple_note`: creates/updates "Groceries" note with HTML checkboxes
  - `delete_reminder`: removes processed reminders
  - Note body builder with category sections

### Support Files
- **requirements.txt** - Python dependencies (Flask, requests, beautifulsoup4)
- **start.sh** - Startup script with health checks
- **test_system.py** - Component tests
- **README.md** - User documentation
- **IMPLEMENTATION.md** - This file

## Data Flow

### Example: Siri → Reminder → Groceries Note

1. **User**: "Hey Siri, remind me to buy pasta, rice, and tomatoes"

2. **Siri**: Creates Apple Reminder with title "Buy pasta, rice, and tomatoes"

3. **Orchestrator** (polling every 20s):
   - Detects new reminder via `RemindersIntegration.list_reminders()`
   - Creates envelope:
     ```json
     {
       "user_id": "local-user",
       "timestamp": "2025-01-15T10:30:00Z",
       "timezone": "America/Los_Angeles",
       "channel": "reminder",
       "mode_hint": "capture",
       "user_text": "Buy pasta, rice, and tomatoes",
       "source_id": "x-apple-reminder://..."
     }
     ```

4. **Brain Client**:
   - Fetches KG context (existing grocery items)
   - Calls Ollama with system prompt + envelope
   - Model returns:
     ```json
     {
       "interaction_intent": "store_only",
       "answer": "",
       "graph_updates": [
         {"op_type": "create_node", "payload": {"type": "GroceryItem", "label": "Pasta", ...}},
         {"op_type": "create_node", "payload": {"type": "GroceryItem", "label": "Rice", ...}},
         {"op_type": "create_node", "payload": {"type": "GroceryItem", "label": "Tomatoes", ...}}
       ],
       "actions": [
         {
           "action_type": "update_apple_note",
           "arguments": {
             "target_folder": "To Buy",
             "target_title": "Groceries",
             "layout": {
               "sections": [
                 {"name": "Pantry & Dry Goods", "items": [{"text": "Pasta"}, {"text": "Rice"}]},
                 {"name": "Produce", "items": [{"text": "Tomatoes"}]}
               ]
             }
           }
         },
         {
           "action_type": "delete_reminder",
           "arguments": {"source_id": "x-apple-reminder://..."}
         }
       ]
     }
     ```

5. **Orchestrator**:
   - Applies `graph_updates` to SQLite KG
   - Executes actions via `ActionExecutor`

6. **Action Executor**:
   - Builds HTML note body with checkboxes:
     ```html
     <div><h1>Groceries</h1><br>
     <h2>Pantry & Dry Goods</h2>
     <ul>
       <li><div><en-todo/>Pasta</div></li>
       <li><div><en-todo/>Rice</div></li>
     </ul>
     <h2>Produce</h2>
     <ul>
       <li><div><en-todo/>Tomatoes</div></li>
     </ul>
     </div>
     ```
   - Calls `NotesIntegration.create_or_update_note()`
   - Calls `RemindersIntegration.delete_reminder()`

7. **Result**:
   - "Groceries" note in "To Buy" folder shows:
     ```
     Groceries

     Pantry & Dry Goods
     ☐ Pasta
     ☐ Rice

     Produce
     ☐ Tomatoes
     ```
   - Original reminder is deleted
   - Interaction logged to `interactions.jsonl`

## Key Design Decisions

### 1. Thin Orchestrator, Smart Model
- The orchestrator is **deterministic glue code** only
- All semantic decisions (categorization, item canonicalization) are in the **model's system prompt**
- This makes the system easy to improve by refining the prompt or fine-tuning the model

### 2. Structured JSON Output
- Model is constrained to return valid JSON with fixed schema
- Fields: `interaction_intent`, `answer`, `graph_updates`, `actions`
- Ollama's `format: "json"` parameter enforces this

### 3. AppleScript Integration
- Uses `osascript` subprocess calls for Reminders/Notes
- Parsing is simplified for PoC (may need refinement for production)
- Permissions are requested automatically by macOS on first access

### 4. Local-First
- Everything runs on the Mac mini
- No cloud API calls for the brain (Ollama is local)
- Knowledge graph is local SQLite
- Works offline (except URL fetching)

### 5. Logging for Training
- Every interaction logged to JSONL: `interactions.jsonl`
- Includes: input envelope, model output, execution results
- Can be used to fine-tune the model later

## Grocery Categories

The system uses 13 fixed categories (defined in brain system prompt):

1. Produce
2. Bakery
3. Meat / Seafood
4. Dairy & Eggs
5. Frozen
6. Pantry & Dry Goods
7. Canned & Jarred
8. Condiments & Sauces
9. Snacks & Sweets
10. Beverages
11. Household & Cleaning
12. Personal Care & Pharmacy
13. Uncategorized / Other

The model assigns items to categories based on semantics, not hard-coded rules.

## Testing

### Quick Smoke Test
```bash
cd ~/workspace/second-brain-poc
source venv/bin/activate
python3 test_system.py
```

This tests each component individually.

### Full Integration Test

1. Start the orchestrator:
   ```bash
   ./start.sh
   ```

2. Create a test reminder via Siri or manually in Reminders app

3. Wait 20 seconds (next poll cycle)

4. Check "To Buy" → "Groceries" note in Apple Notes

5. Verify items appear and original reminder is deleted

### URL Capture Test
```bash
curl -X POST http://localhost:8899/capture/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.allrecipes.com/recipe/21014/good-old-fashioned-pancakes/"}'
```

Check Groceries note for pancake ingredients.

## Current Limitations (PoC Scope)

1. **Model Output Quality**
   - Qwen 2.5 7B sometimes doesn't perfectly follow the layout schema
   - May need prompt refinement or a larger model (14B/32B)
   - Or fine-tuning on interaction logs

2. **AppleScript Parsing**
   - Simplified parsing of AppleScript list output
   - May fail on complex note/reminder structures
   - Production version should use macOS APIs directly (Python objc bindings)

3. **No Deduplication UI**
   - If you add "pasta" multiple times, it appears multiple times
   - Model should deduplicate, but doesn't always
   - Could add server-side deduplication logic

4. **Polling Only**
   - Checks every 20 seconds, not real-time
   - Could use FSEvents or DistributedNotifications for real-time

5. **Single User**
   - Hard-coded `user_id = "local-user"`
   - Multi-user would need authentication layer

6. **No Recipe Storage**
   - Extracts ingredients but doesn't save full recipe
   - Could add Recipe nodes to KG and link to ingredients

## Production Readiness Checklist

To move beyond PoC:

- [ ] Replace AppleScript parsing with proper macOS API bindings
- [ ] Add real-time event listeners (FSEvents, NSDistributedNotificationCenter)
- [ ] Implement proper error handling and retry logic
- [ ] Add unit tests for each module
- [ ] Set up as launchd service for auto-start
- [ ] Add configuration file (instead of hard-coded values)
- [ ] Implement KG query interface for "what's in my pantry?" questions
- [ ] Add web UI for management/debugging
- [ ] Fine-tune model on collected interaction logs
- [ ] Add support for other output formats (shopping list apps, etc.)
- [ ] Implement multi-user support
- [ ] Add recipe management features
- [ ] Integrate with other smart home systems

## Extending the System

### Adding a New Input Channel

1. Add channel detection in `orchestrator._watch_*()` method
2. Create envelope with `channel="new_channel"`
3. Update brain system prompt to handle new channel
4. Test end-to-end

### Adding a New Action Type

1. Define action schema in brain system prompt
2. Implement handler in `action_handlers.ActionExecutor`
3. Model will return new action type automatically

### Adding a New Node Type

1. Define node type in brain system prompt
2. KG automatically handles any node type (no code changes needed)
3. Add specific queries in `kg_database.get_kg_context()` if needed

## Performance

- **Ollama (Qwen 2.5 7B)**: 5-15 seconds per inference on Apple Silicon M-series
- **Polling overhead**: Negligible (<100ms per cycle)
- **AppleScript calls**: 100-500ms each
- **Total latency**: ~20-30 seconds from Siri command to note update

## Storage

- SQLite DB: ~10-50KB for 100s of items
- Interaction logs: ~1-5KB per interaction
- Model: 4.7GB (Qwen 2.5 7B-8B)

## Dependencies

### System
- macOS (for Reminders/Notes)
- Ollama (for local LLM)
- Python 3.9+

### Python Packages
- flask==3.0.0 (HTTP server)
- requests==2.31.0 (URL fetching)
- beautifulsoup4==4.12.2 (HTML parsing)

### Models
- qwen2.5:7b-instruct (via Ollama)

## Conclusion

This PoC successfully demonstrates:
- ✅ Local LLM as decision-making brain
- ✅ Multi-modal input (voice/text/web)
- ✅ Structured output to Apple Notes
- ✅ Knowledge graph persistence
- ✅ Interaction logging for learning

The system is **functional and ready for personal use** as-is, with clear paths for enhancement toward a production system.

# Second Brain PoC: Groceries + Recipes

A proof-of-concept "Second Brain" system that processes groceries and recipes from Apple Reminders, Apple Notes, and URLs, using a local Qwen 2.5 7B-8B LLM to maintain a categorized grocery list in Apple Notes.

## Architecture

- **Brain**: Local Qwen 2.5 7B-8B model (via Ollama)
- **Inputs**: Apple Reminders, Apple Notes, URLs (HTTP endpoint)
- **Output**: Single "Groceries" note in Apple Notes with categorized checklist
- **Storage**: SQLite knowledge graph for items and relationships
- **Logging**: All interactions logged to `interactions.jsonl`

## Prerequisites

- macOS (for Apple Reminders/Notes integration)
- Python 3.9+
- Ollama installed with Qwen 2.5 7B-8B model
- Apple Reminders and Notes apps

## Setup

### 1. Install Ollama and Qwen model

This is already done! Ollama is installed and the model is pulled.

```bash
brew services status ollama  # Should show "started"
ollama list  # Should show qwen2.5:7b-instruct
```

### 2. Install Python dependencies

```bash
cd ~/workspace/second-brain-poc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Note: The virtual environment must be activated before running any Python scripts.

### 3. Grant permissions

The orchestrator needs access to:
- **Reminders**: macOS will prompt when first accessing
- **Notes**: macOS will prompt when first accessing

Grant these permissions when prompted.

## Running the Service

### Start the orchestrator

**Option 1: Use the startup script (recommended)**

```bash
cd ~/workspace/second-brain-poc
./start.sh
```

**Option 2: Manual start**

```bash
cd ~/workspace/second-brain-poc
source venv/bin/activate
python3 orchestrator.py
```

You should see:
```
🧠 Second Brain Orchestrator started
   Polling every 20s
   Watching Reminders and Notes...

🌐 Starting URL capture endpoint on http://localhost:8899
   POST /capture/url with {'url': '...'}
   GET /health for status
```

The service will:
- Poll Apple Reminders every 20 seconds
- Poll Apple Notes every 20 seconds
- Listen for URL capture requests on port 8899

## Testing

### Test 1: Siri → Reminders → Groceries

1. Say to Siri: **"Hey Siri, remind me to buy pasta, rice, and tomatoes"**
2. Wait up to 20 seconds for the orchestrator to detect it
3. Check output: You should see `→ Processing reminder: ...`
4. Open Apple Notes → "To Buy" folder → "Groceries" note
5. Verify the items appear categorized with checkboxes

Expected result:
```
Groceries

Pantry & Dry Goods
☐ Pasta
☐ Rice

Produce
☐ Tomatoes
```

6. The original reminder should be deleted from Reminders app

### Test 2: Recipe in Notes → Groceries

1. Open Apple Notes, create a new note with:
   ```
   Pasta Pomodoro

   Ingredients:
   - 1 box spaghetti
   - 2 cloves garlic
   - 1 can crushed tomatoes
   - Olive oil
   - Fresh basil
   - Salt

   Steps:
   1. Heat oil in a pan
   2. Add garlic and cook until fragrant
   3. Add tomatoes and simmer
   4. Cook pasta and combine
   ```

2. Wait up to 20 seconds
3. Check orchestrator output: `→ Processing apple_note: ...`
4. Open "To Buy" → "Groceries" note
5. Verify the ingredients are added and categorized

### Test 3: URL Capture

1. Find a recipe URL (e.g., from AllRecipes, NYT Cooking, etc.)
2. Send a POST request:
   ```bash
   curl -X POST http://localhost:8899/capture/url \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/recipe-url"}'
   ```

3. Check orchestrator output
4. Verify items appear in Groceries note

### Check health status

```bash
curl http://localhost:8899/health
```

Returns:
```json
{
  "status": "running",
  "reminders_processed": 3,
  "notes_processed": 1
}
```

## Files

- `orchestrator.py` - Main service (polling + HTTP endpoint)
- `kg_database.py` - SQLite knowledge graph layer
- `brain_client.py` - Interface to local Qwen model via Ollama
- `apple_integrations.py` - AppleScript interfaces for Reminders/Notes
- `action_handlers.py` - Execute actions (update note, delete reminder)
- `knowledge_graph.db` - SQLite database (created on first run)
- `interactions.jsonl` - Log of all interactions (for future training)

## Grocery Categories

The brain model uses these standard categories (in order):

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

Items are automatically categorized by the LLM based on semantics.

## Data Flow

```
INPUT (Reminder/Note/URL)
  ↓
Orchestrator detects new item
  ↓
Creates envelope (channel, user_text, source_id, etc.)
  ↓
Gets KG context (existing grocery items)
  ↓
Calls Qwen brain model
  ↓
Brain returns: {graph_updates, actions, answer, interaction_intent}
  ↓
Apply graph_updates to SQLite KG
  ↓
Execute actions (update Groceries note, delete reminder)
  ↓
Log interaction to interactions.jsonl
```

## Logs

All interactions are logged to `interactions.jsonl` with:
- Input envelope
- Model output (graph_updates, actions)
- Execution results
- Any errors

This log can be used for debugging and future model training.

## Stopping the Service

Press `Ctrl+C` in the terminal running the orchestrator.

## Troubleshooting

### Model errors
- Check Ollama is running: `brew services list | grep ollama`
- Test model directly: `ollama run qwen2.5:7b-instruct "Hello"`

### Reminders/Notes not detected
- Check permissions in System Preferences → Privacy & Security
- Increase polling interval if needed (edit `orchestrator.py`)

### Items not categorized correctly
- Check `interactions.jsonl` for model outputs
- The model learns from the system prompt in `brain_client.py`
- Adjust categories or examples in the system prompt

### URL capture fails
- Ensure the URL is publicly accessible
- Check that beautifulsoup4 is installed
- Some sites may block automated requests

## Next Steps (Beyond PoC)

This PoC focuses on groceries + recipes. Future enhancements:

1. Add calendar integration
2. Add Piper voice interface (locally)
3. Add Home Assistant integration
4. Add query mode (ask questions about recipes/inventory)
5. Fine-tune model on interaction logs
6. Add recipe suggestions based on inventory
7. Add meal planning features

## License

This is a proof-of-concept for personal use.

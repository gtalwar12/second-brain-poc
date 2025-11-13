# Second Brain PoC - Quick Start

## Start the System

```bash
cd ~/workspace/second-brain-poc
./start.sh
```

## Use the System

### 1. Via Siri (Voice)
```
"Hey Siri, remind me to buy pasta, rice, and tomatoes"
```
Wait 20 seconds → Check Apple Notes → "To Buy" → "Groceries"

### 2. Via Apple Notes (Recipe)
Create a note with:
```
Pasta Pomodoro

Ingredients:
- Spaghetti
- Tomatoes
- Garlic
- Basil
```
Wait 20 seconds → Check "Groceries" note

### 3. Via URL (Recipe Website)
```bash
curl -X POST http://localhost:8898/capture/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/recipe"}'
```
Check "Groceries" note immediately

## Check Status

```bash
curl http://localhost:8898/health
```

## View Logs

```bash
cd ~/workspace/second-brain-poc
cat interactions.jsonl | jq
```

## Stop the System

Press `Ctrl+C` in the terminal

## Troubleshooting

**Ollama not running?**
```bash
brew services start ollama
```

**Model not found?**
```bash
ollama pull qwen2.5:7b-instruct
```

**Permission denied?**
- Grant Reminders access when prompted
- Grant Notes access when prompted
- Check System Preferences → Privacy & Security

**Items not appearing?**
- Wait at least 20 seconds (polling interval)
- Check orchestrator terminal output
- Check `interactions.jsonl` for errors

## Files

- `orchestrator.py` - Main service
- `knowledge_graph.db` - Item database
- `interactions.jsonl` - Interaction logs
- `README.md` - Full documentation
- `IMPLEMENTATION.md` - Technical details

## That's It!

The system is now running and will automatically:
- Watch for new reminders
- Watch for recipe notes
- Extract grocery items
- Update the "Groceries" note
- Delete processed reminders
- Log everything for future learning

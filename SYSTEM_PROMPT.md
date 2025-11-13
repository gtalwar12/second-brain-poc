# System Prompt for Second Brain PoC

This is the core prompt that instructs the Qwen 2.5 7B-8B model on how to process user inputs and generate structured outputs.

## Prompt Text

```
You are the "Second Brain" - a grocery and recipe assistant.

Your job is to process user inputs and return structured JSON with graph updates and actions.

INPUT FORMAT:
You will receive a JSON envelope with:
- user_id: identifier for the user
- timestamp: when this was captured
- timezone: user's timezone
- channel: "reminder" | "apple_note" | "url_text" | "chat"
- mode_hint: "capture" (store information) | "query" (answer questions)
- user_text: the actual content to process
- source_id: identifier for the source (reminder ID, note ID, or URL)
- kg_context: current knowledge graph context (may be empty)

OUTPUT FORMAT:
You MUST return valid JSON with these exact fields:
{
  "interaction_intent": "store_only" | "answer_only" | "store_and_answer",
  "answer": "<optional text response to user>",
  "graph_updates": [
    {
      "op_type": "create_node" | "update_node" | "create_edge",
      "payload": {
        "id": "<optional node/edge id>",
        "type": "<node/edge type>",
        "label": "<human readable label>",
        "properties": { ... },
        "from_id": "<for edges>",
        "to_id": "<for edges>"
      }
    }
  ],
  "actions": [
    {
      "action_type": "update_apple_note" | "delete_reminder",
      "arguments": { ... }
    }
  ]
}

GROCERY CATEGORIES (use these for the layout sections):
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

YOUR BEHAVIOR:

1. FOR REMINDERS (channel="reminder"):
   - Extract grocery items from the text
   - Create GroceryItem nodes for each item
   - Generate an "update_apple_note" action with:
     - target_folder: "To Buy"
     - target_title: "Groceries"
     - layout: { sections: [ { name: "Category", items: [{text: "Item"}] } ] }
   - Generate a "delete_reminder" action with the source_id
   - Set interaction_intent to "store_only"

2. FOR RECIPE NOTES (channel="apple_note"):
   - Detect if this is a recipe (look for "Ingredients:", list of ingredients, etc.)
   - If it's a recipe:
     - Extract ingredient items (canonical names, no quantities)
     - Create GroceryItem nodes
     - Create a Recipe node
     - Link ingredients to recipe
     - Generate "update_apple_note" action for Groceries note
   - If it's NOT a recipe, ignore it
   - Set interaction_intent to "store_only"

3. FOR URLs (channel="url_text"):
   - Analyze the text
   - If it looks like a recipe or grocery list:
     - Extract items and create nodes
     - Generate "update_apple_note" action
   - Otherwise:
     - Just acknowledge, no actions
   - Set interaction_intent to "store_only"

ITEM CANONICALIZATION:
- Normalize items to singular form
- Remove quantities and measurements
- Use simple, common names
- Examples:
  - "2 boxes of pasta" → "Pasta"
  - "1 can crushed tomatoes" → "Crushed tomatoes"
  - "Fresh basil" → "Basil"

CATEGORY ASSIGNMENT:
- Assign each item to the most appropriate category
- If unsure, use "Uncategorized / Other"
- Group related items together

IMPORTANT:
- Always return valid JSON
- Always include all four top-level fields
- The "layout" in update_apple_note actions should group items by category
- Deduplicate items - only include each canonical item once
- Keep the answer field empty or very brief for capture mode
```

## How This Prompt is Used

This prompt is sent to the Qwen 2.5 7B-8B model (via Ollama) as the **system message** for every interaction.

The model receives:
1. **System prompt** (this prompt)
2. **User message** (containing the envelope with user input + KG context)

And returns structured JSON following the schema defined above.

## Prompt Location in Code

The prompt is defined in `brain_client.py`:

```python
SYSTEM_PROMPT = """You are the "Second Brain" - a grocery and recipe assistant.
...
"""

class BrainClient:
    def call_brain(self, envelope: Dict[str, Any], kg_context: Optional[Dict] = None):
        response = requests.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                ...
            }
        )
```

## Modifying the Prompt

To change the system behavior:

1. Edit `SYSTEM_PROMPT` in `brain_client.py`
2. Restart the orchestrator
3. Test with a sample input
4. Check `interactions.jsonl` to see model outputs

Common modifications:
- Add/remove grocery categories
- Change item canonicalization rules
- Add new action types
- Modify JSON schema
- Add example inputs/outputs for few-shot learning

## Example Model Input

```json
{
  "envelope": {
    "user_id": "local-user",
    "timestamp": "2025-01-15T10:30:00Z",
    "timezone": "America/Los_Angeles",
    "channel": "reminder",
    "mode_hint": "capture",
    "user_text": "Buy pasta, rice, and tomatoes",
    "source_id": "x-apple-reminder://ABC123"
  },
  "kg_context": {
    "grocery_items": []
  }
}
```

## Example Model Output

```json
{
  "interaction_intent": "store_only",
  "answer": "",
  "graph_updates": [
    {
      "op_type": "create_node",
      "payload": {
        "type": "GroceryItem",
        "label": "Pasta",
        "properties": {"category": "Pantry & Dry Goods"}
      }
    },
    {
      "op_type": "create_node",
      "payload": {
        "type": "GroceryItem",
        "label": "Rice",
        "properties": {"category": "Pantry & Dry Goods"}
      }
    },
    {
      "op_type": "create_node",
      "payload": {
        "type": "GroceryItem",
        "label": "Tomatoes",
        "properties": {"category": "Produce"}
      }
    }
  ],
  "actions": [
    {
      "action_type": "update_apple_note",
      "arguments": {
        "target_folder": "To Buy",
        "target_title": "Groceries",
        "layout": {
          "sections": [
            {
              "name": "Pantry & Dry Goods",
              "items": [{"text": "Pasta"}, {"text": "Rice"}]
            },
            {
              "name": "Produce",
              "items": [{"text": "Tomatoes"}]
            }
          ]
        }
      }
    },
    {
      "action_type": "delete_reminder",
      "arguments": {"source_id": "x-apple-reminder://ABC123"}
    }
  ]
}
```

## Prompt Engineering Notes

### What Works Well
- Explicit JSON schema with field descriptions
- Concrete examples in instructions
- Clear behavior per channel (reminder, note, URL)
- Item canonicalization rules with examples
- Fixed category list (prevents hallucination)

### Known Issues with Qwen 2.5 7B
- Sometimes doesn't perfectly follow the layout schema
- May need reminders about deduplication
- Occasionally puts all items in one category
- Can be improved with:
  - Few-shot examples
  - Larger model (14B/32B)
  - Fine-tuning on interaction logs

### Future Improvements
- Add few-shot examples in the prompt
- Include negative examples (what NOT to do)
- Add explicit deduplication instructions
- Fine-tune on collected `interactions.jsonl` logs
- Experiment with different temperature/top_p settings

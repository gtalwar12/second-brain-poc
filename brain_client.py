"""
Brain Client Module
Interface to the local Qwen 2.5 7B-8B model via Ollama.
"""

import json
import requests
from typing import Dict, Any, Optional


SYSTEM_PROMPT = """You are the "Second Brain" - a grocery and recipe assistant.

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
"""


class BrainClient:
    def __init__(self, model_name: str = "qwen2.5:7b-instruct",
                 ollama_url: str = "http://localhost:11434"):
        """Initialize the brain client."""
        self.model_name = model_name
        self.ollama_url = ollama_url

    def call_brain(self, envelope: Dict[str, Any],
                   kg_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Call the local Qwen model with the envelope and return parsed response.
        """
        # Build the user message
        user_message = self._build_user_message(envelope, kg_context)

        # Call Ollama API
        response = requests.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "stream": False,
                "format": "json"
            },
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        # Parse response
        result = response.json()
        message_content = result.get("message", {}).get("content", "{}")

        # Parse the JSON output from the model
        try:
            brain_output = json.loads(message_content)
        except json.JSONDecodeError as e:
            # If model didn't return valid JSON, create a minimal response
            print(f"Warning: Model didn't return valid JSON: {e}")
            print(f"Raw content: {message_content}")
            brain_output = {
                "interaction_intent": "store_only",
                "answer": "",
                "graph_updates": [],
                "actions": []
            }

        # Validate required fields
        required_fields = ["interaction_intent", "answer", "graph_updates", "actions"]
        for field in required_fields:
            if field not in brain_output:
                brain_output[field] = [] if field in ["graph_updates", "actions"] else ""

        return brain_output

    def _build_user_message(self, envelope: Dict, kg_context: Optional[Dict]) -> str:
        """Build the user message from envelope and context."""
        message = {
            "envelope": envelope,
            "kg_context": kg_context or {}
        }
        return json.dumps(message, indent=2)


# Example usage
if __name__ == "__main__":
    # Test the brain client
    client = BrainClient()

    # Test envelope
    test_envelope = {
        "user_id": "local-user",
        "timestamp": "2025-01-15T10:30:00Z",
        "timezone": "America/Los_Angeles",
        "channel": "reminder",
        "mode_hint": "capture",
        "user_text": "Buy pasta, rice, and tomatoes",
        "source_id": "test-reminder-123"
    }

    try:
        result = client.call_brain(test_envelope)
        print("Brain response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

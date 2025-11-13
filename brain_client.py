"""
Brain Client Module
Interface to the local Qwen 2.5 7B-8B model via Ollama.
"""

import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path


def load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    prompt_path = Path(__file__).parent / "prompts" / "brain_system_prompt.md"
    with open(prompt_path, 'r') as f:
        return f.read().strip()


class BrainClient:
    def __init__(self, model_name: str = "qwen2.5:7b-instruct",
                 ollama_url: str = "http://localhost:11434"):
        """Initialize the brain client."""
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.system_prompt = load_system_prompt()

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
                    {"role": "system", "content": self.system_prompt},
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

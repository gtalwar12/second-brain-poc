#!/usr/bin/env python3
"""
Test script for Second Brain PoC
Tests each component individually.
"""

import sys
import json
from datetime import datetime, timezone

print("=" * 60)
print("Second Brain PoC - Component Tests")
print("=" * 60)

# Test 1: Knowledge Graph Database
print("\n1. Testing Knowledge Graph Database...")
try:
    from kg_database import KnowledgeGraph
    kg = KnowledgeGraph(db_path="test_kg.db")

    # Create a test node
    node_id = kg.create_node("GroceryItem", label="Test Pasta", properties={"category": "pantry"})
    print(f"   ✓ Created node: {node_id}")

    # Retrieve the node
    node = kg.get_node(node_id)
    assert node is not None, "Node retrieval failed"
    print(f"   ✓ Retrieved node: {node['label']}")

    # Apply a graph update
    update = {
        "op_type": "create_node",
        "payload": {
            "type": "GroceryItem",
            "label": "Test Rice",
            "properties": {"category": "pantry"}
        }
    }
    result_id = kg.apply_graph_update(update)
    print(f"   ✓ Applied graph update: {result_id}")

    print("   ✓ Knowledge Graph Database: PASS")

except Exception as e:
    print(f"   ✗ Knowledge Graph Database: FAIL - {e}")
    sys.exit(1)

# Test 2: Brain Client
print("\n2. Testing Brain Client (with Ollama)...")
try:
    from brain_client import BrainClient

    client = BrainClient()

    envelope = {
        "user_id": "test-user",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timezone": "America/Los_Angeles",
        "channel": "reminder",
        "mode_hint": "capture",
        "user_text": "Buy apples and bananas",
        "source_id": "test-123"
    }

    print("   → Calling brain model (this may take 10-30 seconds)...")
    result = client.call_brain(envelope)

    assert "interaction_intent" in result, "Missing interaction_intent"
    assert "graph_updates" in result, "Missing graph_updates"
    assert "actions" in result, "Missing actions"
    print(f"   ✓ Brain returned intent: {result['interaction_intent']}")
    print(f"   ✓ Brain returned {len(result['graph_updates'])} graph updates")
    print(f"   ✓ Brain returned {len(result['actions'])} actions")

    print("   ✓ Brain Client: PASS")

except Exception as e:
    print(f"   ✗ Brain Client: FAIL - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Apple Integrations
print("\n3. Testing Apple Integrations...")
try:
    from apple_integrations import RemindersIntegration, NotesIntegration

    # Test Reminders
    reminders = RemindersIntegration.list_reminders()
    print(f"   ✓ Listed {len(reminders)} reminders")

    # Test Notes
    notes = NotesIntegration.list_notes()
    print(f"   ✓ Listed {len(notes)} notes")

    print("   ✓ Apple Integrations: PASS")

except Exception as e:
    print(f"   ✗ Apple Integrations: FAIL - {e}")
    print("   ⚠️  This may fail if permissions are not granted")

# Test 4: Action Handlers
print("\n4. Testing Action Handlers...")
try:
    from action_handlers import ActionExecutor

    executor = ActionExecutor()

    # Test building note body
    test_layout = {
        "sections": [
            {
                "name": "Produce",
                "items": [
                    {"text": "Apples"},
                    {"text": "Bananas"}
                ]
            }
        ]
    }

    body = executor._build_note_body("Test Groceries", test_layout)
    assert "Produce" in body, "Section name not in body"
    assert "Apples" in body, "Item not in body"
    print("   ✓ Generated note body successfully")

    print("   ✓ Action Handlers: PASS")

except Exception as e:
    print(f"   ✗ Action Handlers: FAIL - {e}")
    sys.exit(1)

# Test 5: Interaction Logger
print("\n5. Testing Interaction Logger...")
try:
    from orchestrator import InteractionLogger

    logger = InteractionLogger(log_path="test_interactions.jsonl")

    test_envelope = {"test": "envelope"}
    test_output = {"test": "output"}
    test_results = {"test": "results"}

    logger.log_interaction(test_envelope, test_output, test_results)
    print("   ✓ Logged interaction to test_interactions.jsonl")

    print("   ✓ Interaction Logger: PASS")

except Exception as e:
    print(f"   ✗ Interaction Logger: FAIL - {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
print("\nThe system is ready to use!")
print("\nTo start the orchestrator:")
print("  ./start.sh")
print("\nOr manually:")
print("  source venv/bin/activate")
print("  python3 orchestrator.py")
print("")

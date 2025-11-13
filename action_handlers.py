"""
Action Handlers Module
Execute actions returned by the brain model.
"""

from typing import Dict, Any, List
from apple_integrations import NotesIntegration, RemindersIntegration


class ActionExecutor:
    """Execute actions from the brain model."""

    def __init__(self):
        self.reminders = RemindersIntegration()
        self.notes = NotesIntegration()

    def execute_action(self, action: Dict[str, Any]) -> bool:
        """
        Execute a single action.

        Expected action format:
        {
            "action_type": "update_apple_note" | "delete_reminder",
            "arguments": { ... }
        }
        """
        action_type = action.get('action_type')
        arguments = action.get('arguments', {})

        try:
            if action_type == 'update_apple_note':
                return self._update_apple_note(arguments)

            elif action_type == 'delete_reminder':
                return self._delete_reminder(arguments)

            else:
                print(f"Unknown action type: {action_type}")
                return False

        except Exception as e:
            print(f"Error executing action {action_type}: {e}")
            return False

    def execute_actions(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a list of actions and return results."""
        results = {
            'success_count': 0,
            'failure_count': 0,
            'errors': []
        }

        for action in actions:
            success = self.execute_action(action)
            if success:
                results['success_count'] += 1
            else:
                results['failure_count'] += 1
                results['errors'].append({
                    'action_type': action.get('action_type'),
                    'error': 'Execution failed'
                })

        return results

    def _update_apple_note(self, arguments: Dict[str, Any]) -> bool:
        """
        Update the Groceries note in Apple Notes.

        Expected arguments:
        {
            "target_folder": "To Buy",
            "target_title": "Groceries",
            "layout": {
                "sections": [
                    {
                        "name": "Produce",
                        "items": [
                            {"text": "Tomatoes"},
                            {"text": "Basil"}
                        ]
                    },
                    ...
                ]
            }
        }
        """
        folder_name = arguments.get('target_folder', 'To Buy')
        note_title = arguments.get('target_title', 'Groceries')
        layout = arguments.get('layout', {})

        # Build the note body with checkboxes
        note_body = self._build_note_body(note_title, layout)

        # Create or update the note
        success = self.notes.create_or_update_note(
            folder_name=folder_name,
            note_title=note_title,
            note_body=note_body
        )

        if success:
            print(f"✓ Updated note: {folder_name}/{note_title}")
        else:
            print(f"✗ Failed to update note: {folder_name}/{note_title}")

        return success

    def _build_note_body(self, title: str, layout: Dict[str, Any]) -> str:
        """
        Build the HTML body for the Apple Note with checkboxes.

        Apple Notes uses HTML format. Checkboxes are created using:
        <ul><li><input type="checkbox"> Item text</li></ul>
        """
        sections = layout.get('sections', [])

        # Start with title
        html_parts = [
            f'<div><h1>{title}</h1>',
            '<br>'
        ]

        # Add each section
        for section in sections:
            section_name = section.get('name', 'Uncategorized')
            items = section.get('items', [])

            if not items:
                continue

            # Section header
            html_parts.append(f'<h2>{section_name}</h2>')

            # Checklist items
            html_parts.append('<ul>')
            for item in items:
                item_text = item.get('text', '')
                html_parts.append(f'<li><div><en-todo/>{item_text}</div></li>')
            html_parts.append('</ul>')
            html_parts.append('<br>')

        html_parts.append('</div>')

        return '\n'.join(html_parts)

    def _delete_reminder(self, arguments: Dict[str, Any]) -> bool:
        """
        Delete a reminder.

        Expected arguments:
        {
            "source_id": "<reminder-id>"
        }
        """
        reminder_id = arguments.get('source_id')

        if not reminder_id:
            print("Error: No source_id provided for delete_reminder")
            return False

        success = self.reminders.delete_reminder(reminder_id)

        if success:
            print(f"✓ Deleted reminder: {reminder_id}")
        else:
            print(f"✗ Failed to delete reminder: {reminder_id}")

        return success


# Test function
if __name__ == "__main__":
    # Test building note body
    executor = ActionExecutor()

    test_layout = {
        "sections": [
            {
                "name": "Produce",
                "items": [
                    {"text": "Tomatoes"},
                    {"text": "Basil"},
                    {"text": "Garlic"}
                ]
            },
            {
                "name": "Pantry & Dry Goods",
                "items": [
                    {"text": "Pasta"},
                    {"text": "Rice"}
                ]
            }
        ]
    }

    body = executor._build_note_body("Groceries", test_layout)
    print("Generated note body:")
    print(body)

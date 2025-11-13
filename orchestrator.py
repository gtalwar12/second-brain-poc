"""
Orchestrator Service
Main service that watches Reminders/Notes, calls brain, and executes actions.
"""

import time
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
from pathlib import Path
from flask import Flask, request, jsonify
import threading
import requests
from bs4 import BeautifulSoup

from kg_database import KnowledgeGraph
from brain_client import BrainClient
from apple_integrations import RemindersIntegration, NotesIntegration
from action_handlers import ActionExecutor


class InteractionLogger:
    """Log all interactions to JSONL file."""

    def __init__(self, log_path: str = "interactions.jsonl"):
        self.log_path = log_path

    def log_interaction(self, envelope: Dict, model_output: Dict,
                       execution_results: Dict, errors: Optional[List] = None):
        """Log a single interaction."""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'envelope': envelope,
            'model_output': model_output,
            'execution_results': execution_results,
            'errors': errors or []
        }

        with open(self.log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


class Orchestrator:
    """Main orchestrator service."""

    def __init__(self, poll_interval: int = 20):
        self.poll_interval = poll_interval
        self.kg = KnowledgeGraph()
        self.brain = BrainClient()
        self.executor = ActionExecutor()
        self.logger = InteractionLogger()

        # Track processed items to avoid re-processing
        self.processed_reminders: Set[str] = set()
        self.processed_notes: Dict[str, str] = {}  # note_id -> content_hash

        # Flask app for URL capture
        self.app = Flask(__name__)
        self._setup_routes()

        self.running = False

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/capture/url', methods=['POST'])
        def capture_url():
            """Capture and process a URL."""
            data = request.get_json()
            url = data.get('url')

            if not url:
                return jsonify({'error': 'No URL provided'}), 400

            try:
                # Fetch and process URL
                text = self._fetch_url_text(url)

                # Create envelope
                envelope = self._create_envelope(
                    channel='url_text',
                    user_text=text,
                    source_id=url
                )

                # Process through brain
                self._process_envelope(envelope)

                return jsonify({
                    'success': True,
                    'message': f'Processed URL: {url}'
                })

            except Exception as e:
                return jsonify({
                    'error': str(e)
                }), 500

        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({
                'status': 'running',
                'reminders_processed': len(self.processed_reminders),
                'notes_processed': len(self.processed_notes)
            })

    def _fetch_url_text(self, url: str) -> str:
        """Fetch URL and extract readable text."""
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Use BeautifulSoup for basic text extraction
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def _create_envelope(self, channel: str, user_text: str,
                        source_id: str) -> Dict:
        """Create an envelope for the brain."""
        return {
            'user_id': 'local-user',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'timezone': 'America/Los_Angeles',
            'channel': channel,
            'mode_hint': 'capture',
            'user_text': user_text,
            'source_id': source_id
        }

    def _process_envelope(self, envelope: Dict):
        """Process an envelope through the brain and execute actions."""
        try:
            # Get KG context
            kg_context = self.kg.get_kg_context(context_type='grocery')

            # Call brain
            print(f"\n→ Processing {envelope['channel']}: {envelope['source_id'][:50]}...")
            model_output = self.brain.call_brain(envelope, kg_context)

            # Apply graph updates
            graph_update_results = []
            for update in model_output.get('graph_updates', []):
                try:
                    result_id = self.kg.apply_graph_update(update)
                    graph_update_results.append({'success': True, 'id': result_id})
                except Exception as e:
                    graph_update_results.append({'success': False, 'error': str(e)})
                    print(f"  ✗ Graph update failed: {e}")

            # Execute actions
            actions = model_output.get('actions', [])
            execution_results = self.executor.execute_actions(actions)

            # Log interaction
            self.logger.log_interaction(
                envelope=envelope,
                model_output=model_output,
                execution_results={
                    'graph_updates': graph_update_results,
                    'actions': execution_results
                }
            )

            print(f"  ✓ Processed successfully: {execution_results['success_count']} actions executed")

        except Exception as e:
            print(f"  ✗ Error processing envelope: {e}")
            self.logger.log_interaction(
                envelope=envelope,
                model_output={},
                execution_results={},
                errors=[str(e)]
            )

    def _watch_reminders(self):
        """Watch for new reminders and process them."""
        reminders = RemindersIntegration.list_reminders()

        for reminder in reminders:
            reminder_id = reminder.get('id')
            completed = reminder.get('completed', False)

            # Skip if already processed or completed
            if reminder_id in self.processed_reminders or completed:
                continue

            # Process this reminder
            name = reminder.get('name', '')
            body = reminder.get('body', '')
            user_text = f"{name}. {body}" if body else name

            envelope = self._create_envelope(
                channel='reminder',
                user_text=user_text,
                source_id=reminder_id
            )

            self._process_envelope(envelope)

            # Mark as processed
            self.processed_reminders.add(reminder_id)

    def _watch_notes(self):
        """Watch for new/updated notes and process them."""
        notes = NotesIntegration.list_notes()

        for note in notes:
            note_id = note.get('id')
            name = note.get('name', '')
            body = note.get('body', '')

            # Skip the Groceries note itself
            if name == 'Groceries':
                continue

            # Calculate content hash
            content = f"{name}\n{body}"
            content_hash = hashlib.md5(content.encode()).hexdigest()

            # Skip if already processed with same content
            if note_id in self.processed_notes and self.processed_notes[note_id] == content_hash:
                continue

            # Only process if it looks like it might be a recipe
            # (contains "ingredients" or looks like a list)
            if 'ingredient' in content.lower() or any(c in content for c in ['•', '-', '*']):
                envelope = self._create_envelope(
                    channel='apple_note',
                    user_text=content,
                    source_id=note_id
                )

                self._process_envelope(envelope)

                # Mark as processed
                self.processed_notes[note_id] = content_hash

    def _poll_loop(self):
        """Main polling loop."""
        print(f"\n🧠 Second Brain Orchestrator started")
        print(f"   Polling every {self.poll_interval}s")
        print(f"   Watching Reminders and Notes...")

        while self.running:
            try:
                # Watch reminders
                self._watch_reminders()

                # Watch notes
                self._watch_notes()

            except Exception as e:
                print(f"Error in poll loop: {e}")

            # Sleep before next poll
            time.sleep(self.poll_interval)

    def start(self, port: int = 8898):
        """Start the orchestrator service."""
        self.running = True

        # Start polling in background thread
        poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        poll_thread.start()

        # Start Flask server
        print(f"\n🌐 Starting URL capture endpoint on http://localhost:{port}")
        print(f"   POST /capture/url with {{'url': '...'}}")
        print(f"   GET /health for status\n")

        self.app.run(host='127.0.0.1', port=port, debug=False)

    def stop(self):
        """Stop the orchestrator service."""
        self.running = False


def main():
    """Main entry point."""
    orchestrator = Orchestrator(poll_interval=20)

    try:
        orchestrator.start(port=8898)
    except KeyboardInterrupt:
        print("\n\n⏸️  Shutting down...")
        orchestrator.stop()


if __name__ == "__main__":
    main()

"""
Apple Integrations Module
Interface to Apple Reminders and Apple Notes via AppleScript/osascript.
"""

import subprocess
import json
from typing import List, Dict, Optional


class RemindersIntegration:
    """Interface to Apple Reminders."""

    @staticmethod
    def list_reminders(list_name: Optional[str] = None) -> List[Dict]:
        """
        List all reminders (optionally filtered by list name).
        Returns list of dicts with id, name, body, completed, list_name.
        """
        if list_name:
            script = f'''
                tell application "Reminders"
                    set outputList to {{}}
                    set targetList to list "{list_name}"
                    repeat with r in reminders of targetList
                        set rId to id of r
                        set rName to name of r
                        set rBody to body of r
                        set rCompleted to completed of r
                        set rListName to "{list_name}"
                        set end of outputList to {{rId, rName, rBody, rCompleted, rListName}}
                    end repeat
                    return outputList
                end tell
            '''
        else:
            script = '''
                tell application "Reminders"
                    set outputList to {}
                    repeat with lst in lists
                        set lstName to name of lst
                        repeat with r in reminders of lst
                            set rId to id of r
                            set rName to name of r
                            set rBody to body of r
                            set rCompleted to completed of r
                            set end of outputList to {rId, rName, rBody, rCompleted, lstName}
                        end repeat
                    end repeat
                    return outputList
                end tell
            '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"Error listing reminders: {result.stderr}")
                return []

            # Parse AppleScript list output
            output = result.stdout.strip()
            if not output or output == "":
                return []

            # Parse the AppleScript list format
            reminders = RemindersIntegration._parse_applescript_list(output)
            return reminders

        except Exception as e:
            print(f"Exception listing reminders: {e}")
            return []

    @staticmethod
    def _parse_applescript_list(output: str) -> List[Dict]:
        """Parse AppleScript list output into Python dicts."""
        # AppleScript returns comma-separated values:
        # id, name, body, completed, listName, id, name, body, completed, listName, ...
        reminders = []

        if not output or output.strip() == "":
            return []

        # Split by comma
        parts = [p.strip() for p in output.split(',')]

        # Group into sets of 5 (id, name, body, completed, listName)
        i = 0
        while i + 4 < len(parts):
            reminder = {
                'id': parts[i].strip(),
                'name': parts[i+1].strip(),
                'body': parts[i+2].strip() if parts[i+2].strip() != 'missing value' else '',
                'completed': parts[i+3].strip() == 'true',
                'list_name': parts[i+4].strip()
            }
            reminders.append(reminder)
            i += 5

        return reminders

    @staticmethod
    def delete_reminder(reminder_id: str) -> bool:
        """Delete a reminder by its ID."""
        script = f'''
            tell application "Reminders"
                repeat with lst in lists
                    repeat with r in reminders of lst
                        if id of r is "{reminder_id}" then
                            delete r
                            return true
                        end if
                    end repeat
                end repeat
                return false
            end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            return result.returncode == 0 and 'true' in result.stdout.lower()

        except Exception as e:
            print(f"Exception deleting reminder: {e}")
            return False


class NotesIntegration:
    """Interface to Apple Notes."""

    @staticmethod
    def list_notes(folder_name: Optional[str] = None) -> List[Dict]:
        """
        List all notes (optionally filtered by folder name).
        Returns list of dicts with id, name, body, folder_name, modification_date.
        """
        if folder_name:
            script = f'''
                tell application "Notes"
                    set outputList to {{}}
                    set targetFolder to folder "{folder_name}"
                    repeat with n in notes of targetFolder
                        set nId to id of n
                        set nName to name of n
                        set nBody to body of n
                        set nModDate to modification date of n
                        set end of outputList to {{nId, nName, nBody, "{folder_name}", nModDate as string}}
                    end repeat
                    return outputList
                end tell
            '''
        else:
            script = '''
                tell application "Notes"
                    set outputList to {}
                    repeat with fld in folders
                        set fldName to name of fld
                        repeat with n in notes of fld
                            set nId to id of n
                            set nName to name of n
                            set nBody to body of n
                            set nModDate to modification date of n
                            set end of outputList to {nId, nName, nBody, fldName, nModDate as string}
                        end repeat
                    end repeat
                    return outputList
                end tell
            '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"Error listing notes: {result.stderr}")
                return []

            # Parse AppleScript list output (similar to reminders)
            output = result.stdout.strip()
            if not output:
                return []

            notes = NotesIntegration._parse_applescript_list(output)
            return notes

        except Exception as e:
            print(f"Exception listing notes: {e}")
            return []

    @staticmethod
    def _parse_applescript_list(output: str) -> List[Dict]:
        """Parse AppleScript list output into Python dicts."""
        # Similar to reminders parser, but for notes
        notes = []

        # Remove outer braces
        if output.startswith('{') and output.endswith('}'):
            output = output[1:-1]

        if not output:
            return []

        # This is a simplified parser that may need refinement
        # For PoC, we'll return an empty list and rely on direct API calls
        return notes

    @staticmethod
    def create_or_update_note(folder_name: str, note_title: str,
                             note_body: str) -> bool:
        """
        Create or update a note in the specified folder.
        If a note with the same title exists in the folder, update it.
        Otherwise, create a new note.
        """
        # First, ensure the folder exists
        ensure_folder_script = f'''
            tell application "Notes"
                try
                    set targetFolder to folder "{folder_name}"
                on error
                    make new folder with properties {{name:"{folder_name}"}}
                end try
            end tell
        '''

        subprocess.run(['osascript', '-e', ensure_folder_script],
                      capture_output=True, text=True, timeout=30)

        # Now create or update the note
        # Escape quotes in the body
        escaped_body = note_body.replace('"', '\\"').replace('\n', '\\n')

        script = f'''
            tell application "Notes"
                set targetFolder to folder "{folder_name}"
                set foundNote to missing value

                -- Try to find existing note with this title
                repeat with n in notes of targetFolder
                    if name of n is "{note_title}" then
                        set foundNote to n
                        exit repeat
                    end if
                end repeat

                -- Update or create
                if foundNote is not missing value then
                    -- Update existing note
                    set body of foundNote to "{escaped_body}"
                else
                    -- Create new note
                    make new note at targetFolder with properties {{name:"{note_title}", body:"{escaped_body}"}}
                end if

                return true
            end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            return result.returncode == 0

        except Exception as e:
            print(f"Exception creating/updating note: {e}")
            return False

    @staticmethod
    def get_note(folder_name: str, note_title: str) -> Optional[Dict]:
        """Get a specific note by folder and title."""
        script = f'''
            tell application "Notes"
                set targetFolder to folder "{folder_name}"
                repeat with n in notes of targetFolder
                    if name of n is "{note_title}" then
                        set nId to id of n
                        set nName to name of n
                        set nBody to body of n
                        return {{nId, nName, nBody}}
                    end if
                end repeat
                return missing value
            end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                if 'missing value' not in output:
                    # Parse the result
                    # This is simplified; in production, you'd parse more carefully
                    return {'exists': True, 'content': output}

            return None

        except Exception as e:
            print(f"Exception getting note: {e}")
            return None


# Test functions
if __name__ == "__main__":
    print("Testing Reminders integration...")
    reminders = RemindersIntegration.list_reminders()
    print(f"Found {len(reminders)} reminders")
    for r in reminders[:3]:
        print(f"  - {r.get('name')} ({r.get('list_name')})")

    print("\nTesting Notes integration...")
    notes = NotesIntegration.list_notes()
    print(f"Found {len(notes)} notes")

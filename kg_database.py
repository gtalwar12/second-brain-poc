"""
Knowledge Graph Database Layer
Simple SQLite-based graph database for storing nodes and edges.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class KnowledgeGraph:
    def __init__(self, db_path: str = "knowledge_graph.db"):
        """Initialize the knowledge graph database."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                label TEXT,
                properties TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                properties TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (from_id) REFERENCES nodes (id),
                FOREIGN KEY (to_id) REFERENCES nodes (id)
            )
        """)

        # Create indexes for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id)")

        conn.commit()
        conn.close()

    def create_node(self, node_type: str, label: str = None,
                   properties: Dict = None, node_id: str = None) -> str:
        """Create a new node in the graph."""
        if node_id is None:
            node_id = str(uuid.uuid4())

        now = datetime.utcnow().isoformat()
        properties_json = json.dumps(properties or {})

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO nodes (id, type, label, properties, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (node_id, node_type, label, properties_json, now, now))

        conn.commit()
        conn.close()

        return node_id

    def update_node(self, node_id: str, label: str = None,
                   properties: Dict = None, merge_properties: bool = True):
        """Update an existing node."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get existing node
        cursor.execute("SELECT properties FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise ValueError(f"Node {node_id} not found")

        # Merge or replace properties
        if merge_properties and properties:
            existing_props = json.loads(row[0])
            existing_props.update(properties)
            properties = existing_props

        now = datetime.utcnow().isoformat()
        properties_json = json.dumps(properties or {})

        # Update node
        if label is not None:
            cursor.execute("""
                UPDATE nodes
                SET label = ?, properties = ?, updated_at = ?
                WHERE id = ?
            """, (label, properties_json, now, node_id))
        else:
            cursor.execute("""
                UPDATE nodes
                SET properties = ?, updated_at = ?
                WHERE id = ?
            """, (properties_json, now, node_id))

        conn.commit()
        conn.close()

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Retrieve a node by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, type, label, properties, created_at, updated_at
            FROM nodes WHERE id = ?
        """, (node_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'id': row[0],
            'type': row[1],
            'label': row[2],
            'properties': json.loads(row[3]),
            'created_at': row[4],
            'updated_at': row[5]
        }

    def create_edge(self, edge_type: str, from_id: str, to_id: str,
                   properties: Dict = None, edge_id: str = None) -> str:
        """Create a new edge between two nodes."""
        if edge_id is None:
            edge_id = str(uuid.uuid4())

        now = datetime.utcnow().isoformat()
        properties_json = json.dumps(properties or {})

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO edges (id, type, from_id, to_id, properties, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (edge_id, edge_type, from_id, to_id, properties_json, now, now))

        conn.commit()
        conn.close()

        return edge_id

    def find_nodes_by_type(self, node_type: str, limit: int = 100) -> List[Dict]:
        """Find nodes by type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, type, label, properties, created_at, updated_at
            FROM nodes WHERE type = ?
            ORDER BY updated_at DESC
            LIMIT ?
        """, (node_type, limit))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row[0],
            'type': row[1],
            'label': row[2],
            'properties': json.loads(row[3]),
            'created_at': row[4],
            'updated_at': row[5]
        } for row in rows]

    def apply_graph_update(self, operation: Dict) -> str:
        """
        Apply a graph update operation from the model.

        Expected operation format:
        {
            "op_type": "create_node" | "update_node" | "create_edge",
            "payload": { ... }
        }
        """
        op_type = operation.get('op_type')
        payload = operation.get('payload', {})

        if op_type == 'create_node':
            return self.create_node(
                node_type=payload.get('type'),
                label=payload.get('label'),
                properties=payload.get('properties'),
                node_id=payload.get('id')
            )

        elif op_type == 'update_node':
            self.update_node(
                node_id=payload.get('id'),
                label=payload.get('label'),
                properties=payload.get('properties'),
                merge_properties=payload.get('merge', True)
            )
            return payload.get('id')

        elif op_type == 'create_edge':
            return self.create_edge(
                edge_type=payload.get('type'),
                from_id=payload.get('from_id'),
                to_id=payload.get('to_id'),
                properties=payload.get('properties'),
                edge_id=payload.get('id')
            )

        else:
            raise ValueError(f"Unknown operation type: {op_type}")

    def get_kg_context(self, context_type: str = "grocery", limit: int = 50) -> Dict:
        """
        Get relevant KG context for the model.
        For PoC, just return recent grocery items.
        """
        if context_type == "grocery":
            items = self.find_nodes_by_type("GroceryItem", limit=limit)
            return {
                "grocery_items": items
            }

        return {}

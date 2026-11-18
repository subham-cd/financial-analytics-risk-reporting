"""
FinSight Platform - Database Connection Manager
Provides connection pooling and helper methods for SQLite and PostgreSQL.
"""

import os
import sqlite3
from typing import List, Dict, Any, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "finsight.db")

def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory configured for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    """Executes a SQL query and returns results as a list of dictionaries."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def execute_one(query: str, params: Tuple = ()) -> Dict[str, Any]:
    """Executes a SQL query and returns a single row as a dictionary."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()

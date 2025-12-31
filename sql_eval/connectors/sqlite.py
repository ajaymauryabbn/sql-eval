"""
SQLite Database Connector

Ideal for local testing and bundled sample databases.
"""

import sqlite3
from typing import Optional
from pathlib import Path
from .base import BaseConnector


class SQLiteConnector(BaseConnector):
    """
    SQLite database connector
    
    Great for:
    - Local testing without setup
    - Bundled sample databases
    - Fast evaluation runs
    
    Usage:
        # In-memory database
        conn = SQLiteConnector(":memory:")
        
        # File-based database
        conn = SQLiteConnector("path/to/database.db")
    """
    
    def __init__(
        self,
        database: str = ":memory:",
        timeout: float = 30.0,
        **kwargs
    ):
        super().__init__(connection_string=database, **kwargs)
        self.database = database
        self.timeout = timeout
        self._connection: Optional[sqlite3.Connection] = None
    
    @property
    def db_type(self) -> str:
        return "sqlite"
    
    def connect(self) -> None:
        """Connect to SQLite database"""
        self._connection = sqlite3.connect(
            self.database,
            timeout=self.timeout
        )
        # Enable foreign keys
        self._connection.execute("PRAGMA foreign_keys = ON")
        # Return rows as dictionaries
        self._connection.row_factory = sqlite3.Row
    
    def disconnect(self) -> None:
        """Close SQLite connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """Execute SQL and return results as list of dicts"""
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor()
        
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # Check if query returns results
            if cursor.description:
                rows = cursor.fetchall()
                # Convert Row objects to dicts
                return [dict(row) for row in rows]
            else:
                self._connection.commit()
                return []
        finally:
            cursor.close()
    
    def execute_script(self, sql_script: str) -> None:
        """Execute multiple SQL statements"""
        if not self._connection:
            self.connect()
        
        self._connection.executescript(sql_script)
        self._connection.commit()
    
    def get_schema(self) -> dict:
        """Extract schema from SQLite database"""
        if not self._connection:
            self.connect()
        
        schema = {'tables': {}}
        
        # Get all tables
        tables = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        
        for table in tables:
            table_name = table['name']
            columns = {}
            foreign_keys = []
            
            # Get column info
            col_info = self.execute(f"PRAGMA table_info('{table_name}')")
            for col in col_info:
                columns[col['name']] = {
                    'type': col['type'],
                    'nullable': not col['notnull'],
                    'primary_key': bool(col['pk']),
                    'default': col['dflt_value']
                }
            
            # Get foreign keys
            fk_info = self.execute(f"PRAGMA foreign_key_list('{table_name}')")
            for fk in fk_info:
                foreign_keys.append({
                    'column': fk['from'],
                    'references': f"{fk['table']}.{fk['to']}"
                })
            
            schema['tables'][table_name] = {
                'columns': columns,
                'foreign_keys': foreign_keys
            }
        
        return schema
    
    def load_schema_file(self, filepath: str) -> None:
        """Load schema from SQL file"""
        with open(filepath, 'r') as f:
            schema_sql = f.read()
        self.execute_script(schema_sql)
    
    def load_seed_data(self, filepath: str) -> None:
        """Load seed data from SQL file"""
        with open(filepath, 'r') as f:
            seed_sql = f.read()
        self.execute_script(seed_sql)
    
    @classmethod
    def from_files(
        cls,
        schema_file: str,
        seed_file: str = None,
        database: str = ":memory:"
    ) -> "SQLiteConnector":
        """
        Create connector and load schema/seed data
        
        Args:
            schema_file: Path to SQL file with CREATE TABLE statements
            seed_file: Optional path to SQL file with INSERT statements
            database: Database path (default: in-memory)
            
        Returns:
            Configured SQLiteConnector
        """
        connector = cls(database=database)
        connector.connect()
        connector.load_schema_file(schema_file)
        
        if seed_file and Path(seed_file).exists():
            connector.load_seed_data(seed_file)
        
        return connector

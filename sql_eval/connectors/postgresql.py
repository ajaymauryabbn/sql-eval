"""
PostgreSQL Database Connector
"""

import os
from typing import Optional
from .base import BaseConnector


class PostgreSQLConnector(BaseConnector):
    """
    PostgreSQL database connector
    
    Usage:
        # Using connection string
        conn = PostgreSQLConnector(
            connection_string="postgresql://user:pass@localhost:5432/mydb"
        )
        
        # Using individual parameters
        conn = PostgreSQLConnector(
            host="localhost",
            port=5432,
            database="mydb",
            user="user",
            password="pass"
        )
    """
    
    def __init__(
        self,
        connection_string: str = None,
        host: str = None,
        port: int = 5432,
        database: str = None,
        user: str = None,
        password: str = None,
        **kwargs
    ):
        super().__init__(connection_string=connection_string, **kwargs)
        
        # Allow individual params or connection string
        self.host = host or os.environ.get("PGHOST", "localhost")
        self.port = port or int(os.environ.get("PGPORT", 5432))
        self.database = database or os.environ.get("PGDATABASE")
        self.user = user or os.environ.get("PGUSER")
        self.password = password or os.environ.get("PGPASSWORD")
        
        self._connection = None
    
    @property
    def db_type(self) -> str:
        return "postgresql"
    
    def connect(self) -> None:
        """Connect to PostgreSQL database"""
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise ImportError(
                "psycopg2 not installed. "
                "Install with: pip install psycopg2-binary"
            )
        
        if self.connection_string:
            self._connection = psycopg2.connect(self.connection_string)
        else:
            self._connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
    
    def disconnect(self) -> None:
        """Close PostgreSQL connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """Execute SQL and return results as list of dicts"""
        if not self._connection:
            self.connect()
        
        import psycopg2.extras
        
        cursor = self._connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # Check if query returns results
            if cursor.description:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                self._connection.commit()
                return []
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def get_schema(self) -> dict:
        """Extract schema from PostgreSQL database"""
        if not self._connection:
            self.connect()
        
        schema = {'tables': {}}
        
        # Get all tables
        tables = self.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        for table in tables:
            table_name = table['table_name']
            columns = {}
            foreign_keys = []
            
            # Get column info
            col_info = self.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            for col in col_info:
                columns[col['column_name']] = {
                    'type': col['data_type'].upper(),
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default']
                }
            
            # Get primary keys
            pk_info = self.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.table_name = %s
                AND tc.constraint_type = 'PRIMARY KEY'
            """, (table_name,))
            
            for pk in pk_info:
                if pk['column_name'] in columns:
                    columns[pk['column_name']]['primary_key'] = True
            
            # Get foreign keys
            fk_info = self.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.table_name = %s
                AND tc.constraint_type = 'FOREIGN KEY'
            """, (table_name,))
            
            for fk in fk_info:
                foreign_keys.append({
                    'column': fk['column_name'],
                    'references': f"{fk['foreign_table']}.{fk['foreign_column']}"
                })
            
            schema['tables'][table_name] = {
                'columns': columns,
                'foreign_keys': foreign_keys
            }
        
        return schema

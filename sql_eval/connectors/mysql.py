"""
MySQL Database Connector
"""

import os
from typing import Optional

from .base import BaseConnector


class MySQLConnector(BaseConnector):
    """
    MySQL database connector

    Usage:
        # Using connection string
        conn = MySQLConnector(
            connection_string="mysql://user:pass@localhost:3306/mydb"
        )

        # Using individual parameters
        conn = MySQLConnector(
            host="localhost",
            port=3306,
            database="mydb",
            user="user",
            password="pass"
        )
    """

    def __init__(
        self,
        connection_string: str = None,
        host: str = None,
        port: int = 3306,
        database: str = None,
        user: str = None,
        password: str = None,
        **kwargs
    ):
        super().__init__(connection_string=connection_string, **kwargs)

        self.host = host or os.environ.get("MYSQL_HOST", "localhost")
        self.port = port or int(os.environ.get("MYSQL_PORT", 3306))
        self.database = database or os.environ.get("MYSQL_DATABASE")
        self.user = user or os.environ.get("MYSQL_USER")
        self.password = password or os.environ.get("MYSQL_PASSWORD")

        self._connection = None

    @property
    def db_type(self) -> str:
        return "mysql"

    def connect(self) -> None:
        """Connect to MySQL database"""
        try:
            import mysql.connector
        except ImportError:
            raise ImportError(
                "mysql-connector-python not installed. "
                "Install with: pip install mysql-connector-python"
            )

        self._connection = mysql.connector.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def disconnect(self) -> None:
        """Close MySQL connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """Execute SQL and return results as list of dicts"""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor(dictionary=True)

        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            # Check if query returns results
            if cursor.description:
                rows = cursor.fetchall()
                return list(rows)
            else:
                self._connection.commit()
                return []
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()

    def get_schema(self) -> dict:
        """Extract schema from MySQL database"""
        if not self._connection:
            self.connect()

        schema = {'tables': {}}

        # Get all tables
        tables = self.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_type = 'BASE TABLE'
        """)

        for table in tables:
            table_name = table['TABLE_NAME'] if 'TABLE_NAME' in table else table['table_name']
            columns = {}
            foreign_keys = []

            # Get column info
            col_info = self.execute(f"""
                SELECT
                    COLUMN_NAME as column_name,
                    DATA_TYPE as data_type,
                    IS_NULLABLE as is_nullable,
                    COLUMN_DEFAULT as column_default,
                    COLUMN_KEY as column_key
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = '{table_name}'
                ORDER BY ordinal_position
            """)

            for col in col_info:
                col_name = col.get('column_name') or col.get('COLUMN_NAME')
                columns[col_name] = {
                    'type': (col.get('data_type') or col.get('DATA_TYPE', '')).upper(),
                    'nullable': (col.get('is_nullable') or col.get('IS_NULLABLE')) == 'YES',
                    'primary_key': (col.get('column_key') or col.get('COLUMN_KEY')) == 'PRI',
                    'default': col.get('column_default') or col.get('COLUMN_DEFAULT')
                }

            # Get foreign keys
            fk_info = self.execute(f"""
                SELECT
                    COLUMN_NAME as column_name,
                    REFERENCED_TABLE_NAME as ref_table,
                    REFERENCED_COLUMN_NAME as ref_column
                FROM information_schema.key_column_usage
                WHERE table_schema = DATABASE()
                AND table_name = '{table_name}'
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """)

            for fk in fk_info:
                col_name = fk.get('column_name') or fk.get('COLUMN_NAME')
                ref_table = fk.get('ref_table') or fk.get('REFERENCED_TABLE_NAME')
                ref_column = fk.get('ref_column') or fk.get('REFERENCED_COLUMN_NAME')
                foreign_keys.append({
                    'column': col_name,
                    'references': f"{ref_table}.{ref_column}"
                })

            schema['tables'][table_name] = {
                'columns': columns,
                'foreign_keys': foreign_keys
            }

        return schema

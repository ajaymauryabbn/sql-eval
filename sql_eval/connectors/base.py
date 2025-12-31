"""
Base class for database connectors
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseConnector(ABC):
    """Abstract base class for database connectors"""

    def __init__(self, connection_string: str = None, **kwargs):
        self.connection_string = connection_string
        self.config = kwargs
        self._connection = None

    @property
    @abstractmethod
    def db_type(self) -> str:
        """Return database type (e.g., 'postgresql', 'mysql')"""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    def execute(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """
        Execute SQL query and return results

        Args:
            sql: SQL query to execute
            params: Optional query parameters

        Returns:
            List of dictionaries (each dict is a row)
        """
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """
        Extract schema from database

        Returns:
            Dictionary with tables and columns info
        """
        pass

    def execute_safe(
        self,
        sql: str,
        timeout_seconds: int = 30
    ) -> tuple[bool, Optional[list[dict]], Optional[str]]:
        """
        Execute SQL with timeout and error handling

        Returns:
            Tuple of (success, results, error_message)
        """
        try:
            results = self.execute(sql)
            return True, results, None
        except Exception as e:
            return False, None, str(e)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

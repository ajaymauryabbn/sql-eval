"""
Database connectors for sql-eval
"""

from .base import BaseConnector
from .sqlite import SQLiteConnector
from .postgresql import PostgreSQLConnector
from .mysql import MySQLConnector


def get_connector(
    db_type: str,
    connection_string: str = None,
    **kwargs
) -> BaseConnector:
    """
    Factory function to get database connector by type
    
    Args:
        db_type: One of 'sqlite', 'postgresql', 'mysql'
        connection_string: Database connection string
        **kwargs: Additional connector-specific arguments
        
    Returns:
        Configured database connector instance
    """
    connectors = {
        'sqlite': SQLiteConnector,
        'postgresql': PostgreSQLConnector,
        'postgres': PostgreSQLConnector,
        'pg': PostgreSQLConnector,
        'mysql': MySQLConnector,
    }
    
    db_type = db_type.lower()
    
    if db_type not in connectors:
        available = ', '.join(set(connectors.keys()))
        raise ValueError(
            f"Unknown database type: {db_type}. "
            f"Available types: {available}"
        )
    
    connector_class = connectors[db_type]
    
    if connection_string:
        return connector_class(connection_string=connection_string, **kwargs)
    return connector_class(**kwargs)


__all__ = [
    "BaseConnector",
    "SQLiteConnector",
    "PostgreSQLConnector",
    "MySQLConnector",
    "get_connector"
]

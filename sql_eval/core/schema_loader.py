"""
Schema loading from various sources
"""

import re
import json
from pathlib import Path
from typing import Optional, Union
from .models import TableSchema, DatabaseSchema


class SchemaLoader:
    """Load database schema from various sources"""
    
    @staticmethod
    def from_sql_file(filepath: Union[str, Path]) -> DatabaseSchema:
        """
        Parse CREATE TABLE statements from SQL file
        
        Args:
            filepath: Path to .sql file with CREATE TABLE statements
            
        Returns:
            DatabaseSchema object
        """
        with open(filepath, 'r') as f:
            sql_content = f.read()
        return SchemaLoader.from_ddl(sql_content)
    
    @staticmethod
    def from_ddl(ddl_string: str) -> DatabaseSchema:
        """
        Parse CREATE TABLE statements from DDL string
        
        Args:
            ddl_string: String containing CREATE TABLE statements
            
        Returns:
            DatabaseSchema object
        """
        tables = {}
        relationships = []
        
        # Find all CREATE TABLE statements
        create_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?(\w+)[`"\']?\s*\((.*?)\);'
        matches = re.findall(create_pattern, ddl_string, re.IGNORECASE | re.DOTALL)
        
        for table_name, columns_str in matches:
            table_name = table_name.lower()
            columns = {}
            foreign_keys = []
            
            # Split by comma, but handle nested parentheses
            column_defs = SchemaLoader._split_column_definitions(columns_str)
            
            for col_def in column_defs:
                col_def = col_def.strip()
                if not col_def:
                    continue
                
                # Check for constraints
                if col_def.upper().startswith('PRIMARY KEY'):
                    continue
                elif col_def.upper().startswith('FOREIGN KEY'):
                    fk = SchemaLoader._parse_foreign_key(col_def)
                    if fk:
                        foreign_keys.append(fk)
                        relationships.append({
                            'from_table': table_name,
                            'from_column': fk['column'],
                            'to_table': fk['references'].split('.')[0],
                            'to_column': fk['references'].split('.')[1] if '.' in fk['references'] else 'id'
                        })
                elif col_def.upper().startswith('UNIQUE'):
                    continue
                elif col_def.upper().startswith('CHECK'):
                    continue
                elif col_def.upper().startswith('CONSTRAINT'):
                    continue
                else:
                    # Parse column definition
                    col_info = SchemaLoader._parse_column(col_def)
                    if col_info:
                        columns[col_info['name']] = col_info['details']
            
            tables[table_name] = TableSchema(
                name=table_name,
                columns=columns,
                foreign_keys=foreign_keys
            )
        
        return DatabaseSchema(tables=tables, relationships=relationships)
    
    @staticmethod
    def from_json(filepath: Union[str, Path]) -> DatabaseSchema:
        """
        Load schema from JSON file
        
        Expected format:
        {
            "tables": {
                "users": {
                    "columns": {
                        "id": {"type": "INTEGER", "primary_key": true},
                        "name": {"type": "VARCHAR(100)"}
                    },
                    "foreign_keys": []
                }
            }
        }
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        tables = {}
        for table_name, table_data in data.get('tables', {}).items():
            tables[table_name] = TableSchema(
                name=table_name,
                columns=table_data.get('columns', {}),
                foreign_keys=table_data.get('foreign_keys', []),
                description=table_data.get('description')
            )
        
        return DatabaseSchema(
            tables=tables,
            relationships=data.get('relationships', [])
        )
    
    @staticmethod
    def from_dict(schema_dict: dict) -> DatabaseSchema:
        """Load schema from a dictionary"""
        tables = {}
        for table_name, table_data in schema_dict.get('tables', {}).items():
            if isinstance(table_data, TableSchema):
                tables[table_name] = table_data
            else:
                tables[table_name] = TableSchema(
                    name=table_name,
                    columns=table_data.get('columns', {}),
                    foreign_keys=table_data.get('foreign_keys', []),
                    description=table_data.get('description')
                )
        
        return DatabaseSchema(
            tables=tables,
            relationships=schema_dict.get('relationships', [])
        )
    
    @staticmethod
    def _split_column_definitions(columns_str: str) -> list[str]:
        """Split column definitions handling nested parentheses"""
        result = []
        current = ""
        depth = 0
        
        for char in columns_str:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                result.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            result.append(current.strip())
        
        return result
    
    @staticmethod
    def _parse_column(col_def: str) -> Optional[dict]:
        """Parse a single column definition"""
        # Match: column_name TYPE [(size)] [constraints...]
        pattern = r'^[`"\']?(\w+)[`"\']?\s+(\w+)(?:\s*\(([^)]+)\))?\s*(.*)?$'
        match = re.match(pattern, col_def.strip(), re.IGNORECASE)
        
        if not match:
            return None
        
        col_name = match.group(1).lower()
        col_type = match.group(2).upper()
        col_size = match.group(3)
        constraints = match.group(4) or ""
        
        # Build full type string
        if col_size:
            full_type = f"{col_type}({col_size})"
        else:
            full_type = col_type
        
        details = {
            'type': full_type,
            'nullable': 'NOT NULL' not in constraints.upper(),
            'primary_key': 'PRIMARY KEY' in constraints.upper()
        }
        
        # Check for default value
        default_match = re.search(r'DEFAULT\s+([^\s,]+)', constraints, re.IGNORECASE)
        if default_match:
            details['default'] = default_match.group(1)
        
        # Check for references (inline foreign key)
        ref_match = re.search(r'REFERENCES\s+(\w+)\s*\(\s*(\w+)\s*\)', constraints, re.IGNORECASE)
        if ref_match:
            details['references'] = f"{ref_match.group(1)}.{ref_match.group(2)}"
        
        return {'name': col_name, 'details': details}
    
    @staticmethod
    def _parse_foreign_key(fk_def: str) -> Optional[dict]:
        """Parse a foreign key constraint"""
        pattern = r'FOREIGN\s+KEY\s*\(\s*[`"\']?(\w+)[`"\']?\s*\)\s*REFERENCES\s+[`"\']?(\w+)[`"\']?\s*\(\s*[`"\']?(\w+)[`"\']?\s*\)'
        match = re.search(pattern, fk_def, re.IGNORECASE)
        
        if match:
            return {
                'column': match.group(1).lower(),
                'references': f"{match.group(2).lower()}.{match.group(3).lower()}"
            }
        return None


class SchemaValidator:
    """Validate database schema for common issues"""
    
    @staticmethod
    def validate(schema: DatabaseSchema) -> list[str]:
        """
        Validate schema and return list of warnings/errors
        """
        issues = []
        
        # Check for empty schema
        if not schema.tables:
            issues.append("ERROR: Schema has no tables")
            return issues
        
        # Check each table
        for table_name, table in schema.tables.items():
            # Check for empty tables
            if not table.columns:
                issues.append(f"WARNING: Table '{table_name}' has no columns")
            
            # Check for primary key
            has_pk = any(
                col.get('primary_key', False) 
                for col in table.columns.values()
            )
            if not has_pk:
                issues.append(f"WARNING: Table '{table_name}' has no primary key")
            
            # Validate foreign keys
            for fk in table.foreign_keys:
                ref_table = fk['references'].split('.')[0]
                if ref_table not in schema.tables:
                    issues.append(
                        f"ERROR: Foreign key in '{table_name}' references "
                        f"non-existent table '{ref_table}'"
                    )
        
        return issues

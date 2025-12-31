"""
SQL parsing and comparison utilities
"""

import re
from typing import Optional

from .models import PartialScores

try:
    import sqlparse
    HAS_SQLPARSE = True
except ImportError:
    HAS_SQLPARSE = False


class SQLParser:
    """Parse SQL queries and extract components"""

    @staticmethod
    def normalize(sql: str) -> str:
        """
        Normalize SQL for comparison
        - Uppercase keywords
        - Lowercase identifiers
        - Remove extra whitespace
        - Remove trailing semicolon
        """
        if not sql:
            return ""

        if HAS_SQLPARSE:
            normalized = sqlparse.format(
                sql,
                keyword_case='upper',
                identifier_case='lower',
                strip_whitespace=True,
                reindent=False
            )
        else:
            # Basic normalization without sqlparse
            normalized = ' '.join(sql.split())
            # Uppercase common keywords
            keywords = [
                'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'JOIN', 'LEFT', 'RIGHT',
                'INNER', 'OUTER', 'ON', 'GROUP', 'BY', 'ORDER', 'ASC', 'DESC',
                'LIMIT', 'OFFSET', 'HAVING', 'UNION', 'ALL', 'DISTINCT', 'AS',
                'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'IN', 'NOT', 'NULL', 'IS',
                'BETWEEN', 'LIKE', 'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
            ]
            for kw in keywords:
                normalized = re.sub(
                    rf'\b{kw}\b',
                    kw,
                    normalized,
                    flags=re.IGNORECASE
                )

        return normalized.strip().rstrip(';').strip()

    @staticmethod
    def extract_components(sql: str) -> dict:
        """
        Extract SQL components for structural comparison

        Returns:
            dict with keys: tables, columns, joins, where_conditions,
                           group_by, order_by, aggregations, limit
        """
        sql = sql.strip()
        if not sql:
            return SQLParser._empty_components()

        components = {
            'tables': [],
            'columns': [],
            'joins': [],
            'where_conditions': [],
            'group_by': [],
            'order_by': [],
            'aggregations': [],
            'limit': None,
            'distinct': False,
            'subqueries': []
        }

        sql_upper = sql.upper()

        # Check for DISTINCT
        components['distinct'] = 'DISTINCT' in sql_upper

        # Extract tables from FROM clause
        components['tables'] = SQLParser._extract_tables(sql)

        # Extract columns from SELECT clause
        components['columns'] = SQLParser._extract_select_columns(sql)

        # Extract JOINs
        components['joins'] = SQLParser._extract_joins(sql)

        # Extract WHERE conditions
        components['where_conditions'] = SQLParser._extract_where(sql)

        # Extract GROUP BY
        components['group_by'] = SQLParser._extract_group_by(sql)

        # Extract ORDER BY
        components['order_by'] = SQLParser._extract_order_by(sql)

        # Extract aggregations
        components['aggregations'] = SQLParser._extract_aggregations(sql)

        # Extract LIMIT
        components['limit'] = SQLParser._extract_limit(sql)

        return components

    @staticmethod
    def _empty_components() -> dict:
        return {
            'tables': [],
            'columns': [],
            'joins': [],
            'where_conditions': [],
            'group_by': [],
            'order_by': [],
            'aggregations': [],
            'limit': None,
            'distinct': False,
            'subqueries': []
        }

    @staticmethod
    def _extract_tables(sql: str) -> list[str]:
        """Extract table names from FROM clause and JOINs"""
        tables = set()

        # Match FROM table
        from_match = re.search(
            r'\bFROM\s+([`"\']?\w+[`"\']?(?:\s+(?:AS\s+)?\w+)?)',
            sql,
            re.IGNORECASE
        )
        if from_match:
            table = from_match.group(1).split()[0].strip('`"\'').lower()
            tables.add(table)

        # Match JOIN tables
        join_pattern = r'\bJOIN\s+([`"\']?\w+[`"\']?)'
        for match in re.finditer(join_pattern, sql, re.IGNORECASE):
            tables.add(match.group(1).strip('`"\'').lower())

        return sorted(list(tables))

    @staticmethod
    def _extract_select_columns(sql: str) -> list[str]:
        """Extract column names from SELECT clause"""
        columns = []

        # Find SELECT ... FROM
        select_match = re.search(
            r'\bSELECT\s+(.*?)\s+FROM\b',
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if not select_match:
            return columns

        select_clause = select_match.group(1)

        # Handle SELECT *
        if select_clause.strip() == '*':
            return ['*']

        # Split by comma (handling nested parentheses)
        parts = SQLParser._split_by_comma(select_clause)

        for part in parts:
            part = part.strip()
            # Get alias or column name
            as_match = re.search(r'\bAS\s+([`"\']?\w+[`"\']?)$', part, re.IGNORECASE)
            if as_match:
                columns.append(as_match.group(1).strip('`"\'').lower())
            else:
                # Get last identifier
                identifiers = re.findall(r'[`"\']?(\w+)[`"\']?', part)
                if identifiers:
                    columns.append(identifiers[-1].lower())

        return columns

    @staticmethod
    def _extract_joins(sql: str) -> list[dict]:
        """Extract JOIN information"""
        joins = []

        join_pattern = r'(LEFT\s+|RIGHT\s+|INNER\s+|OUTER\s+|FULL\s+|CROSS\s+)?JOIN\s+([`"\']?\w+[`"\']?)(?:\s+(?:AS\s+)?(\w+))?\s+ON\s+([^JOIN]+?)(?=(?:LEFT|RIGHT|INNER|OUTER|FULL|CROSS)?\s*JOIN|\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|$)'

        for match in re.finditer(join_pattern, sql, re.IGNORECASE | re.DOTALL):
            join_type = (match.group(1) or '').strip().upper() or 'INNER'
            table = match.group(2).strip('`"\'').lower()
            alias = match.group(3).lower() if match.group(3) else None
            condition = match.group(4).strip()

            joins.append({
                'type': join_type + ' JOIN',
                'table': table,
                'alias': alias,
                'condition': SQLParser._normalize_condition(condition)
            })

        return joins

    @staticmethod
    def _extract_where(sql: str) -> list[str]:
        """Extract WHERE conditions"""
        conditions = []

        where_match = re.search(
            r'\bWHERE\s+(.*?)(?:\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|\bHAVING\b|$)',
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if where_match:
            where_clause = where_match.group(1).strip()
            # Split by AND/OR (simplified)
            parts = re.split(r'\s+AND\s+|\s+OR\s+', where_clause, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if part:
                    conditions.append(SQLParser._normalize_condition(part))

        return conditions

    @staticmethod
    def _extract_group_by(sql: str) -> list[str]:
        """Extract GROUP BY columns"""
        columns = []

        match = re.search(
            r'\bGROUP\s+BY\s+(.*?)(?:\bHAVING\b|\bORDER\s+BY\b|\bLIMIT\b|$)',
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            group_clause = match.group(1).strip()
            parts = SQLParser._split_by_comma(group_clause)
            for part in parts:
                part = part.strip().lower()
                # Extract just the column name
                identifiers = re.findall(r'[`"\']?(\w+)[`"\']?', part)
                if identifiers:
                    columns.append(identifiers[-1])

        return columns

    @staticmethod
    def _extract_order_by(sql: str) -> list[dict]:
        """Extract ORDER BY columns"""
        order = []

        match = re.search(
            r'\bORDER\s+BY\s+(.*?)(?:\bLIMIT\b|$)',
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            order_clause = match.group(1).strip()
            parts = SQLParser._split_by_comma(order_clause)
            for part in parts:
                part = part.strip()
                direction = 'ASC'
                if re.search(r'\bDESC\b', part, re.IGNORECASE):
                    direction = 'DESC'
                # Get column name
                col_match = re.match(r'([^\s]+)', part)
                if col_match:
                    col = col_match.group(1).strip('`"\'').lower()
                    order.append({'column': col, 'direction': direction})

        return order

    @staticmethod
    def _extract_aggregations(sql: str) -> list[str]:
        """Extract aggregation functions used"""
        aggs = set()

        agg_pattern = r'\b(COUNT|SUM|AVG|MIN|MAX|GROUP_CONCAT|STRING_AGG)\s*\('
        for match in re.finditer(agg_pattern, sql, re.IGNORECASE):
            aggs.add(match.group(1).upper())

        return sorted(list(aggs))

    @staticmethod
    def _extract_limit(sql: str) -> Optional[int]:
        """Extract LIMIT value"""
        match = re.search(r'\bLIMIT\s+(\d+)', sql, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _split_by_comma(text: str) -> list[str]:
        """Split by comma, respecting parentheses"""
        parts = []
        current = ""
        depth = 0

        for char in text:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            parts.append(current.strip())

        return parts

    @staticmethod
    def _normalize_condition(condition: str) -> str:
        """Normalize a condition for comparison"""
        # Remove extra whitespace
        condition = ' '.join(condition.split())
        # Lowercase
        condition = condition.lower()
        # Standardize operators
        condition = re.sub(r'\s*=\s*', ' = ', condition)
        condition = re.sub(r'\s*<>\s*', ' != ', condition)
        condition = re.sub(r'\s*!=\s*', ' != ', condition)
        condition = re.sub(r'\s*>=\s*', ' >= ', condition)
        condition = re.sub(r'\s*<=\s*', ' <= ', condition)
        condition = re.sub(r'\s*>\s*', ' > ', condition)
        condition = re.sub(r'\s*<\s*', ' < ', condition)
        return condition.strip()


class SQLComparator:
    """Compare SQL queries at multiple levels"""

    def __init__(self):
        self.parser = SQLParser()

    def exact_match(self, sql1: str, sql2: str) -> bool:
        """Check if two SQL queries are identical (normalized)"""
        norm1 = SQLParser.normalize(sql1)
        norm2 = SQLParser.normalize(sql2)
        return norm1 == norm2

    def structural_match(self, sql1: str, sql2: str) -> PartialScores:
        """
        Compare SQL structure and return partial scores
        """
        comp1 = SQLParser.extract_components(sql1)
        comp2 = SQLParser.extract_components(sql2)

        scores = PartialScores()

        # Compare tables (order-insensitive)
        scores.tables_match = set(comp1['tables']) == set(comp2['tables'])

        # Compare columns (order-insensitive, handle * expansion)
        cols1 = set(comp1['columns'])
        cols2 = set(comp2['columns'])
        if '*' in cols1 or '*' in cols2:
            # If either uses *, consider it a partial match
            scores.columns_match = bool(cols1 & cols2) or (cols1 == cols2)
        else:
            scores.columns_match = cols1 == cols2

        # Compare JOINs
        scores.joins_match = self._compare_joins(comp1['joins'], comp2['joins'])

        # Compare WHERE conditions (relaxed matching)
        scores.where_match = self._compare_conditions(
            comp1['where_conditions'],
            comp2['where_conditions']
        )

        # Compare GROUP BY
        scores.groupby_match = set(comp1['group_by']) == set(comp2['group_by'])

        # Compare ORDER BY
        scores.orderby_match = self._compare_order_by(
            comp1['order_by'],
            comp2['order_by']
        )

        # Compare aggregations
        scores.aggregations_match = set(comp1['aggregations']) == set(comp2['aggregations'])

        # Calculate overall score
        weights = {
            'tables_match': 0.20,
            'columns_match': 0.20,
            'joins_match': 0.15,
            'where_match': 0.20,
            'groupby_match': 0.10,
            'orderby_match': 0.05,
            'aggregations_match': 0.10
        }

        scores.overall_score = sum(
            weights[key] * (1.0 if getattr(scores, key) else 0.0)
            for key in weights
        )

        return scores

    def _compare_joins(self, joins1: list, joins2: list) -> bool:
        """Compare JOIN clauses"""
        if len(joins1) != len(joins2):
            return False

        if not joins1:
            return True

        # Compare tables being joined (order might differ)
        tables1 = {j['table'] for j in joins1}
        tables2 = {j['table'] for j in joins2}

        return tables1 == tables2

    def _compare_conditions(self, conds1: list, conds2: list) -> bool:
        """Compare WHERE conditions (relaxed matching)"""
        if not conds1 and not conds2:
            return True

        if len(conds1) != len(conds2):
            return False

        # Normalize and compare as sets
        set1 = set(conds1)
        set2 = set(conds2)

        return set1 == set2

    def _compare_order_by(self, order1: list, order2: list) -> bool:
        """Compare ORDER BY clauses"""
        if len(order1) != len(order2):
            return False

        if not order1:
            return True

        # Order matters for ORDER BY
        for o1, o2 in zip(order1, order2):
            if o1['column'] != o2['column']:
                return False
            if o1['direction'] != o2['direction']:
                return False

        return True

    def get_differences(self, sql1: str, sql2: str) -> list[str]:
        """Get human-readable list of differences"""
        differences = []

        comp1 = SQLParser.extract_components(sql1)
        comp2 = SQLParser.extract_components(sql2)

        # Check tables
        tables1 = set(comp1['tables'])
        tables2 = set(comp2['tables'])
        if tables1 != tables2:
            missing = tables2 - tables1
            extra = tables1 - tables2
            if missing:
                differences.append(f"Missing tables: {missing}")
            if extra:
                differences.append(f"Extra tables: {extra}")

        # Check columns
        cols1 = set(comp1['columns'])
        cols2 = set(comp2['columns'])
        if cols1 != cols2:
            missing = cols2 - cols1
            extra = cols1 - cols2
            if missing:
                differences.append(f"Missing columns: {missing}")
            if extra:
                differences.append(f"Extra columns: {extra}")

        # Check JOINs
        if len(comp1['joins']) != len(comp2['joins']):
            differences.append(
                f"JOIN count mismatch: {len(comp1['joins'])} vs {len(comp2['joins'])}"
            )

        # Check GROUP BY
        gb1 = set(comp1['group_by'])
        gb2 = set(comp2['group_by'])
        if gb1 != gb2:
            differences.append(f"GROUP BY mismatch: {gb1} vs {gb2}")

        # Check aggregations
        agg1 = set(comp1['aggregations'])
        agg2 = set(comp2['aggregations'])
        if agg1 != agg2:
            differences.append(f"Aggregation mismatch: {agg1} vs {agg2}")

        return differences

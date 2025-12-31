"""
Tests for sql-eval core functionality
"""

import pytest

from sql_eval.core.models import (
    DatabaseSchema,
    EvaluationCase,
    EvaluationResult,
    PartialScores,
    QueryStatus,
    TableSchema,
)
from sql_eval.core.schema_loader import SchemaLoader
from sql_eval.core.sql_parser import SQLComparator, SQLParser


class TestSQLParser:
    """Tests for SQL parsing functionality"""

    def test_normalize_basic(self):
        sql = "select * from users"
        normalized = SQLParser.normalize(sql)
        assert "SELECT" in normalized
        assert "FROM" in normalized

    def test_normalize_removes_semicolon(self):
        sql = "SELECT * FROM users;"
        normalized = SQLParser.normalize(sql)
        assert not normalized.endswith(';')

    def test_extract_tables_single(self):
        sql = "SELECT * FROM users"
        components = SQLParser.extract_components(sql)
        assert 'users' in components['tables']

    def test_extract_tables_with_join(self):
        sql = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        components = SQLParser.extract_components(sql)
        assert 'users' in components['tables']
        assert 'orders' in components['tables']

    def test_extract_columns_star(self):
        sql = "SELECT * FROM users"
        components = SQLParser.extract_components(sql)
        assert '*' in components['columns']

    def test_extract_columns_specific(self):
        sql = "SELECT id, name, email FROM users"
        components = SQLParser.extract_components(sql)
        assert 'id' in components['columns']
        assert 'name' in components['columns']
        assert 'email' in components['columns']

    def test_extract_aggregations(self):
        sql = "SELECT COUNT(*), SUM(amount) FROM orders"
        components = SQLParser.extract_components(sql)
        assert 'COUNT' in components['aggregations']
        assert 'SUM' in components['aggregations']

    def test_extract_group_by(self):
        sql = "SELECT category, COUNT(*) FROM products GROUP BY category"
        components = SQLParser.extract_components(sql)
        assert 'category' in components['group_by']

    def test_extract_order_by(self):
        sql = "SELECT * FROM products ORDER BY price DESC"
        components = SQLParser.extract_components(sql)
        assert len(components['order_by']) == 1
        assert components['order_by'][0]['direction'] == 'DESC'

    def test_extract_limit(self):
        sql = "SELECT * FROM users LIMIT 10"
        components = SQLParser.extract_components(sql)
        assert components['limit'] == 10


class TestSQLComparator:
    """Tests for SQL comparison functionality"""

    def setup_method(self):
        self.comparator = SQLComparator()

    def test_exact_match_identical(self):
        sql1 = "SELECT * FROM users"
        sql2 = "SELECT * FROM users"
        assert self.comparator.exact_match(sql1, sql2)

    def test_exact_match_case_insensitive(self):
        sql1 = "SELECT * FROM users"
        sql2 = "select * from users"
        assert self.comparator.exact_match(sql1, sql2)

    def test_exact_match_whitespace_insensitive(self):
        sql1 = "SELECT * FROM users"
        sql2 = "SELECT  *  FROM  users"
        assert self.comparator.exact_match(sql1, sql2)

    def test_exact_match_different(self):
        sql1 = "SELECT * FROM users"
        sql2 = "SELECT * FROM orders"
        assert not self.comparator.exact_match(sql1, sql2)

    def test_structural_match_tables(self):
        sql1 = "SELECT id FROM users"
        sql2 = "SELECT name FROM users"
        scores = self.comparator.structural_match(sql1, sql2)
        assert scores.tables_match
        assert not scores.columns_match

    def test_structural_match_joins(self):
        sql1 = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        sql2 = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        scores = self.comparator.structural_match(sql1, sql2)
        assert scores.tables_match
        assert scores.joins_match

    def test_get_differences(self):
        sql1 = "SELECT id FROM users"
        sql2 = "SELECT name FROM orders"
        diffs = self.comparator.get_differences(sql1, sql2)
        assert len(diffs) > 0


class TestSchemaLoader:
    """Tests for schema loading functionality"""

    def test_parse_simple_table(self):
        ddl = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255)
        );
        """
        schema = SchemaLoader.from_ddl(ddl)
        assert 'users' in schema.tables
        assert 'id' in schema.tables['users'].columns
        assert 'name' in schema.tables['users'].columns
        assert 'email' in schema.tables['users'].columns

    def test_parse_primary_key(self):
        ddl = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        );
        """
        schema = SchemaLoader.from_ddl(ddl)
        assert schema.tables['users'].columns['id']['primary_key']

    def test_parse_foreign_key(self):
        ddl = """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
        schema = SchemaLoader.from_ddl(ddl)
        assert len(schema.tables['orders'].foreign_keys) == 1
        assert schema.tables['orders'].foreign_keys[0]['column'] == 'user_id'

    def test_parse_multiple_tables(self):
        ddl = """
        CREATE TABLE users (id INTEGER PRIMARY KEY);
        CREATE TABLE orders (id INTEGER PRIMARY KEY);
        CREATE TABLE products (id INTEGER PRIMARY KEY);
        """
        schema = SchemaLoader.from_ddl(ddl)
        assert len(schema.tables) == 3

    def test_to_prompt_string(self):
        ddl = "CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100));"
        schema = SchemaLoader.from_ddl(ddl)
        prompt_str = schema.to_prompt_string()
        assert 'users' in prompt_str
        assert 'id' in prompt_str
        assert 'name' in prompt_str


class TestModels:
    """Tests for data models"""

    def test_evaluation_case_creation(self):
        case = EvaluationCase(
            question_id="Q001",
            natural_language_question="How many users?",
            ground_truth_sql="SELECT COUNT(*) FROM users",
            difficulty="easy",
            category="aggregation"
        )
        assert case.question_id == "Q001"
        assert case.difficulty == "easy"

    def test_evaluation_result_to_dict(self):
        result = EvaluationResult(
            question_id="Q001",
            question="How many users?",
            ground_truth_sql="SELECT COUNT(*) FROM users",
            generated_sql="SELECT COUNT(*) FROM users",
            status=QueryStatus.SUCCESS,
            exact_match=True,
            latency_ms=150.5
        )
        d = result.to_dict()
        assert d['question_id'] == "Q001"
        assert d['exact_match']
        assert d['status'] == 'success'

    def test_partial_scores_to_dict(self):
        scores = PartialScores(
            tables_match=True,
            columns_match=True,
            joins_match=False,
            overall_score=0.75
        )
        d = scores.to_dict()
        assert d['tables_match']
        assert not d['joins_match']
        assert d['overall_score'] == 0.75


class TestDatabaseSchema:
    """Tests for DatabaseSchema class"""

    def test_to_ddl_string(self):
        schema = DatabaseSchema(
            tables={
                'users': TableSchema(
                    name='users',
                    columns={
                        'id': {'type': 'INTEGER', 'primary_key': True},
                        'name': {'type': 'VARCHAR(100)', 'nullable': False}
                    }
                )
            }
        )
        ddl = schema.to_ddl_string()
        assert 'CREATE TABLE users' in ddl
        assert 'id INTEGER PRIMARY KEY' in ddl


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

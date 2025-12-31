"""
Bundled datasets for sql-eval
"""

import json
from pathlib import Path
from typing import Tuple

from ..connectors.sqlite import SQLiteConnector
from ..core.evaluator import DatasetLoader
from ..core.models import DatabaseSchema, EvaluationCase
from ..core.schema_loader import SchemaLoader

DATASETS_DIR = Path(__file__).parent


def list_datasets() -> list[str]:
    """List all available bundled datasets"""
    datasets = []
    for path in DATASETS_DIR.iterdir():
        if path.is_dir() and (path / 'schema.sql').exists():
            datasets.append(path.name)
    return datasets


def load_dataset(
    name: str,
    with_db: bool = False
) -> Tuple[list[EvaluationCase], DatabaseSchema, SQLiteConnector]:
    """
    Load a bundled dataset

    Args:
        name: Dataset name (e.g., 'ecommerce')
        with_db: Whether to create SQLite database with seed data

    Returns:
        Tuple of (test_cases, schema, db_connector or None)
    """
    dataset_path = DATASETS_DIR / name

    if not dataset_path.exists():
        available = list_datasets()
        raise ValueError(
            f"Dataset '{name}' not found. "
            f"Available datasets: {available}"
        )

    # Load schema
    schema_file = dataset_path / 'schema.sql'
    schema = SchemaLoader.from_sql_file(schema_file)

    # Load test cases
    questions_file = dataset_path / 'questions.json'
    if questions_file.exists():
        test_cases = DatasetLoader.from_json(questions_file)
    else:
        questions_csv = dataset_path / 'questions.csv'
        if questions_csv.exists():
            test_cases = DatasetLoader.from_csv(questions_csv)
        else:
            raise ValueError(f"No questions file found in {dataset_path}")

    # Optionally create database
    db_connector = None
    if with_db:
        seed_file = dataset_path / 'seed_data.sql'
        db_connector = SQLiteConnector.from_files(
            schema_file=str(schema_file),
            seed_file=str(seed_file) if seed_file.exists() else None
        )

    return test_cases, schema, db_connector


def get_dataset_info(name: str) -> dict:
    """Get information about a dataset"""
    dataset_path = DATASETS_DIR / name

    if not dataset_path.exists():
        raise ValueError(f"Dataset '{name}' not found")

    # Count questions
    questions_file = dataset_path / 'questions.json'
    if questions_file.exists():
        with open(questions_file, 'r') as f:
            questions = json.load(f)
        num_questions = len(questions)

        # Count by difficulty
        difficulty_counts = {}
        category_counts = {}
        for q in questions:
            diff = q.get('difficulty', 'unknown')
            cat = q.get('category', 'unknown')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            category_counts[cat] = category_counts.get(cat, 0) + 1
    else:
        num_questions = 0
        difficulty_counts = {}
        category_counts = {}

    # Count tables in schema
    schema_file = dataset_path / 'schema.sql'
    schema = SchemaLoader.from_sql_file(schema_file)
    num_tables = len(schema.tables)

    return {
        'name': name,
        'path': str(dataset_path),
        'num_questions': num_questions,
        'num_tables': num_tables,
        'tables': list(schema.tables.keys()),
        'difficulty_breakdown': difficulty_counts,
        'category_breakdown': category_counts,
        'has_seed_data': (dataset_path / 'seed_data.sql').exists()
    }


# Convenience function for quick access
def load_ecommerce(with_db: bool = False):
    """Load the e-commerce sample dataset"""
    return load_dataset('ecommerce', with_db=with_db)


__all__ = [
    'list_datasets',
    'load_dataset',
    'get_dataset_info',
    'load_ecommerce'
]

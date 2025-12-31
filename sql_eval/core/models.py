"""
Data models for sql-eval framework
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QueryStatus(Enum):
    """Status of SQL generation/execution"""
    SUCCESS = "success"
    SYNTAX_ERROR = "syntax_error"
    EXECUTION_ERROR = "execution_error"
    GENERATION_ERROR = "generation_error"
    TIMEOUT = "timeout"


class Difficulty(Enum):
    """Question difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Category(Enum):
    """SQL question categories"""
    SIMPLE_SELECT = "simple_select"
    FILTER = "filter"
    AGGREGATION = "aggregation"
    GROUPBY = "groupby"
    ORDERBY = "orderby"
    JOINS = "joins"
    SUBQUERY = "subquery"
    WINDOW_FUNCTIONS = "window_functions"
    DATE_FUNCTIONS = "date_functions"
    STRING_FUNCTIONS = "string_functions"
    COMPLEX = "complex"


@dataclass
class TableSchema:
    """Schema for a single table"""
    name: str
    columns: dict[str, dict]  # column_name -> {type, nullable, primary_key, etc.}
    foreign_keys: list[dict] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class DatabaseSchema:
    """Complete database schema"""
    tables: dict[str, TableSchema]
    relationships: list[dict] = field(default_factory=list)

    def to_prompt_string(self) -> str:
        """Convert schema to string format for LLM prompts"""
        lines = []
        for table_name, table in self.tables.items():
            lines.append(f"TABLE: {table_name}")
            if table.description:
                lines.append(f"  Description: {table.description}")
            lines.append("  Columns:")
            for col_name, col_info in table.columns.items():
                col_str = f"    - {col_name}: {col_info.get('type', 'UNKNOWN')}"
                if col_info.get('primary_key'):
                    col_str += " (PRIMARY KEY)"
                if col_info.get('nullable') is False:
                    col_str += " NOT NULL"
                lines.append(col_str)

            if table.foreign_keys:
                lines.append("  Foreign Keys:")
                for fk in table.foreign_keys:
                    lines.append(f"    - {fk['column']} -> {fk['references']}")
            lines.append("")

        return "\n".join(lines)

    def to_ddl_string(self) -> str:
        """Convert schema to CREATE TABLE statements"""
        statements = []
        for table_name, table in self.tables.items():
            cols = []
            for col_name, col_info in table.columns.items():
                col_def = f"  {col_name} {col_info.get('type', 'TEXT')}"
                if col_info.get('primary_key'):
                    col_def += " PRIMARY KEY"
                if col_info.get('nullable') is False:
                    col_def += " NOT NULL"
                if col_info.get('default') is not None:
                    col_def += f" DEFAULT {col_info['default']}"
                cols.append(col_def)

            for fk in table.foreign_keys:
                cols.append(f"  FOREIGN KEY ({fk['column']}) REFERENCES {fk['references']}")

            stmt = f"CREATE TABLE {table_name} (\n" + ",\n".join(cols) + "\n);"
            statements.append(stmt)

        return "\n\n".join(statements)


@dataclass
class EvaluationCase:
    """Single test case for evaluation"""
    question_id: str
    natural_language_question: str
    ground_truth_sql: str
    difficulty: str = "medium"  # easy, medium, hard
    category: str = "complex"   # joins, aggregations, filters, etc.
    tags: list[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class PartialScores:
    """Detailed breakdown of SQL comparison"""
    tables_match: bool = False
    columns_match: bool = False
    joins_match: bool = False
    where_match: bool = False
    groupby_match: bool = False
    orderby_match: bool = False
    aggregations_match: bool = False
    overall_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "tables_match": self.tables_match,
            "columns_match": self.columns_match,
            "joins_match": self.joins_match,
            "where_match": self.where_match,
            "groupby_match": self.groupby_match,
            "orderby_match": self.orderby_match,
            "aggregations_match": self.aggregations_match,
            "overall_score": self.overall_score
        }


@dataclass
class EvaluationResult:
    """Result for a single test case"""
    question_id: str
    question: str
    ground_truth_sql: str
    generated_sql: str
    status: QueryStatus

    # Core metrics
    exact_match: bool = False
    execution_match: bool = False
    partial_scores: Optional[PartialScores] = None

    # Execution details
    ground_truth_result: Optional[list] = None
    generated_result: Optional[list] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0

    # Metadata from test case
    difficulty: str = "medium"
    category: str = "complex"

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "ground_truth_sql": self.ground_truth_sql,
            "generated_sql": self.generated_sql,
            "status": self.status.value,
            "exact_match": self.exact_match,
            "execution_match": self.execution_match,
            "partial_scores": self.partial_scores.to_dict() if self.partial_scores else None,
            "error_message": self.error_message,
            "latency_ms": self.latency_ms,
            "difficulty": self.difficulty,
            "category": self.category
        }


@dataclass
class FailurePattern:
    """Common failure pattern identified in evaluation"""
    pattern_name: str
    description: str
    count: int
    example_question_ids: list[str]
    suggestion: Optional[str] = None


@dataclass
class EvaluationReport:
    """Complete evaluation report"""
    # Summary metrics
    total_questions: int
    exact_match_accuracy: float
    execution_accuracy: float
    structural_accuracy: float
    avg_latency_ms: float

    # Breakdown
    accuracy_by_category: dict[str, dict]
    accuracy_by_difficulty: dict[str, dict]

    # Error analysis
    common_failure_patterns: list[FailurePattern]

    # Individual results
    results: list[EvaluationResult]

    # Metadata
    llm_provider: str = ""
    llm_model: str = ""
    dataset_name: str = ""
    timestamp: str = ""

    def get_summary(self) -> str:
        """Get a text summary of the report"""
        lines = [
            "=" * 50,
            "EVALUATION SUMMARY",
            "=" * 50,
            f"Total Questions: {self.total_questions}",
            f"Exact Match Accuracy: {self.exact_match_accuracy:.1%}",
            f"Execution Accuracy: {self.execution_accuracy:.1%}",
            f"Structural Accuracy: {self.structural_accuracy:.1%}",
            f"Average Latency: {self.avg_latency_ms:.0f}ms",
            "",
            "BY DIFFICULTY:",
        ]

        for diff, stats in self.accuracy_by_difficulty.items():
            lines.append(f"  {diff}: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})")

        lines.append("")
        lines.append("BY CATEGORY:")
        for cat, stats in self.accuracy_by_category.items():
            lines.append(f"  {cat}: {stats['accuracy']:.1%} ({stats['correct']}/{stats['total']})")

        if self.common_failure_patterns:
            lines.append("")
            lines.append("COMMON FAILURE PATTERNS:")
            for i, pattern in enumerate(self.common_failure_patterns[:5], 1):
                lines.append(f"  {i}. {pattern.pattern_name} ({pattern.count} cases)")

        lines.append("=" * 50)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "summary": {
                "total_questions": self.total_questions,
                "exact_match_accuracy": self.exact_match_accuracy,
                "execution_accuracy": self.execution_accuracy,
                "structural_accuracy": self.structural_accuracy,
                "avg_latency_ms": self.avg_latency_ms
            },
            "accuracy_by_category": self.accuracy_by_category,
            "accuracy_by_difficulty": self.accuracy_by_difficulty,
            "failure_patterns": [
                {
                    "pattern": p.pattern_name,
                    "count": p.count,
                    "description": p.description
                }
                for p in self.common_failure_patterns
            ],
            "results": [r.to_dict() for r in self.results],
            "metadata": {
                "llm_provider": self.llm_provider,
                "llm_model": self.llm_model,
                "dataset_name": self.dataset_name,
                "timestamp": self.timestamp
            }
        }

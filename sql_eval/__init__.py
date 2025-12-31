"""
sql-eval: Open-source Text-to-SQL Evaluation Framework

Measure how good your Text-to-SQL actually is.
"""

__version__ = "0.1.0"
__author__ = "Ajay Maurya"

from sql_eval.core.evaluator import Evaluator
from sql_eval.core.models import EvaluationCase, EvaluationReport, EvaluationResult

__all__ = [
    "Evaluator",
    "EvaluationCase",
    "EvaluationResult",
    "EvaluationReport",
]

"""
Main evaluation engine for sql-eval
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

from ..connectors.base import BaseConnector
from ..llm_providers.base import BaseLLMProvider
from .models import (
    DatabaseSchema,
    EvaluationCase,
    EvaluationReport,
    EvaluationResult,
    FailurePattern,
    QueryStatus,
)
from .sql_parser import SQLComparator, SQLParser


class Evaluator:
    """
    Main evaluation engine for Text-to-SQL systems

    Usage:
        from sql_eval import Evaluator
        from sql_eval.llm_providers import OpenAIProvider

        provider = OpenAIProvider()
        evaluator = Evaluator(llm_provider=provider, schema=schema)
        report = evaluator.evaluate(test_cases)
        print(report.get_summary())
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        schema: DatabaseSchema = None,
        db_connector: Optional[BaseConnector] = None,
        few_shot_examples: Optional[list[dict]] = None,
        verbose: bool = True
    ):
        self.llm = llm_provider
        self.schema = schema
        self.db = db_connector
        self.few_shot_examples = few_shot_examples or []
        self.verbose = verbose
        self.comparator = SQLComparator()
        self.parser = SQLParser()

    def evaluate(
        self,
        test_cases: list[EvaluationCase],
        run_execution_tests: bool = True,
        few_shot_examples: Optional[list[dict]] = None
    ) -> EvaluationReport:
        """Run full evaluation on test cases"""
        if not self.schema:
            raise ValueError("Schema is required for evaluation")

        examples = few_shot_examples or self.few_shot_examples
        results = []

        if self.verbose:
            self._print_header(len(test_cases))

        for i, case in enumerate(test_cases):
            result = self._evaluate_single(
                case,
                run_execution=run_execution_tests and self.db is not None,
                examples=examples
            )
            results.append(result)

            if self.verbose:
                self._print_progress(i + 1, len(test_cases), result)

        report = self._generate_report(results)

        if self.verbose:
            print("\n" + report.get_summary())

        return report

    def evaluate_single(
        self,
        question: str,
        ground_truth_sql: str,
        run_execution: bool = True,
        examples: Optional[list[dict]] = None
    ) -> EvaluationResult:
        """Evaluate a single question"""
        case = EvaluationCase(
            question_id="single",
            natural_language_question=question,
            ground_truth_sql=ground_truth_sql
        )
        return self._evaluate_single(
            case,
            run_execution=run_execution and self.db is not None,
            examples=examples or self.few_shot_examples
        )

    def _evaluate_single(
        self,
        case: EvaluationCase,
        run_execution: bool,
        examples: list[dict]
    ) -> EvaluationResult:
        """Evaluate a single test case"""
        start_time = time.time()
        generated_sql = ""
        status = QueryStatus.SUCCESS
        error_msg = None

        try:
            generated_sql = self.llm.generate_sql(
                question=case.natural_language_question,
                schema=self.schema,
                examples=examples
            )
        except Exception as e:
            status = QueryStatus.GENERATION_ERROR
            error_msg = str(e)

        latency_ms = (time.time() - start_time) * 1000

        exact_match = False
        if status == QueryStatus.SUCCESS:
            exact_match = self.comparator.exact_match(
                generated_sql,
                case.ground_truth_sql
            )

        partial_scores = None
        if status == QueryStatus.SUCCESS:
            partial_scores = self.comparator.structural_match(
                generated_sql,
                case.ground_truth_sql
            )

        execution_match = False
        gt_result = None
        gen_result = None

        if run_execution and status == QueryStatus.SUCCESS:
            execution_match, gt_result, gen_result, exec_error = self._compare_execution(
                generated_sql,
                case.ground_truth_sql
            )
            if exec_error and not error_msg:
                error_msg = exec_error
                status = QueryStatus.EXECUTION_ERROR

        return EvaluationResult(
            question_id=case.question_id,
            question=case.natural_language_question,
            ground_truth_sql=case.ground_truth_sql,
            generated_sql=generated_sql,
            status=status,
            exact_match=exact_match,
            execution_match=execution_match,
            partial_scores=partial_scores,
            ground_truth_result=gt_result,
            generated_result=gen_result,
            error_message=error_msg,
            latency_ms=latency_ms,
            difficulty=case.difficulty,
            category=case.category
        )

    def _compare_execution(
        self,
        generated_sql: str,
        ground_truth_sql: str
    ) -> tuple[bool, Optional[list], Optional[list], Optional[str]]:
        """Execute both queries and compare results"""
        try:
            gt_result = self.db.execute(ground_truth_sql)
            gen_result = self.db.execute(generated_sql)
            match = self._results_equal(gt_result, gen_result)
            return match, gt_result, gen_result, None
        except Exception as e:
            return False, None, None, str(e)

    def _results_equal(
        self,
        result1: list[dict],
        result2: list[dict]
    ) -> bool:
        """Compare query results (order-insensitive by default)"""
        if result1 is None or result2 is None:
            return result1 == result2

        if len(result1) != len(result2):
            return False

        if not result1:
            return True

        def normalize_row(row):
            return tuple(sorted((str(k).lower(), str(v)) for k, v in row.items()))

        set1 = set(normalize_row(r) for r in result1)
        set2 = set(normalize_row(r) for r in result2)

        return set1 == set2

    def _generate_report(self, results: list[EvaluationResult]) -> EvaluationReport:
        """Generate summary report from results"""
        total = len(results)

        exact_matches = sum(1 for r in results if r.exact_match)
        execution_matches = sum(1 for r in results if r.execution_match)
        structural_matches = sum(
            1 for r in results
            if r.partial_scores and r.partial_scores.overall_score >= 0.8
        )

        avg_latency = sum(r.latency_ms for r in results) / total if total else 0

        accuracy_by_difficulty = self._group_accuracy(results, 'difficulty')
        accuracy_by_category = self._group_accuracy(results, 'category')
        failure_patterns = self._analyze_failures(results)

        return EvaluationReport(
            total_questions=total,
            exact_match_accuracy=exact_matches / total if total else 0,
            execution_accuracy=execution_matches / total if total else 0,
            structural_accuracy=structural_matches / total if total else 0,
            avg_latency_ms=avg_latency,
            accuracy_by_category=accuracy_by_category,
            accuracy_by_difficulty=accuracy_by_difficulty,
            common_failure_patterns=failure_patterns,
            results=results,
            llm_provider=self.llm.provider_name,
            llm_model=self.llm.model,
            timestamp=datetime.now().isoformat()
        )

    def _group_accuracy(
        self,
        results: list[EvaluationResult],
        group_by: str
    ) -> dict[str, dict]:
        """Group accuracy by difficulty or category"""
        groups = defaultdict(lambda: {'correct': 0, 'total': 0})

        for r in results:
            key = getattr(r, group_by, 'unknown')
            groups[key]['total'] += 1
            if r.exact_match:
                groups[key]['correct'] += 1

        for key in groups:
            total = groups[key]['total']
            correct = groups[key]['correct']
            groups[key]['accuracy'] = correct / total if total else 0

        return dict(groups)

    def _analyze_failures(self, results: list[EvaluationResult]) -> list[FailurePattern]:
        """Analyze common failure patterns"""
        patterns = defaultdict(lambda: {'count': 0, 'examples': []})

        for r in results:
            if r.exact_match or r.status != QueryStatus.SUCCESS:
                continue

            if not r.partial_scores:
                continue

            if not r.partial_scores.tables_match:
                patterns['wrong_tables']['count'] += 1
                patterns['wrong_tables']['examples'].append(r.question_id)

            if not r.partial_scores.columns_match:
                patterns['wrong_columns']['count'] += 1
                patterns['wrong_columns']['examples'].append(r.question_id)

            if not r.partial_scores.joins_match:
                patterns['wrong_joins']['count'] += 1
                patterns['wrong_joins']['examples'].append(r.question_id)

            if not r.partial_scores.where_match:
                patterns['wrong_conditions']['count'] += 1
                patterns['wrong_conditions']['examples'].append(r.question_id)

            if not r.partial_scores.groupby_match:
                patterns['wrong_groupby']['count'] += 1
                patterns['wrong_groupby']['examples'].append(r.question_id)

            if not r.partial_scores.aggregations_match:
                patterns['wrong_aggregations']['count'] += 1
                patterns['wrong_aggregations']['examples'].append(r.question_id)

        pattern_descriptions = {
            'wrong_tables': 'Incorrect table selection',
            'wrong_columns': 'Missing or incorrect columns in SELECT',
            'wrong_joins': 'Incorrect JOIN type or missing JOINs',
            'wrong_conditions': 'Incorrect WHERE conditions',
            'wrong_groupby': 'Missing or incorrect GROUP BY',
            'wrong_aggregations': 'Wrong aggregation functions'
        }

        failure_patterns = []
        for name, data in sorted(patterns.items(), key=lambda x: -x[1]['count']):
            if data['count'] > 0:
                failure_patterns.append(FailurePattern(
                    pattern_name=name,
                    description=pattern_descriptions.get(name, name),
                    count=data['count'],
                    example_question_ids=data['examples'][:5]
                ))

        return failure_patterns

    def _print_header(self, total: int):
        """Print evaluation header"""
        print("\n" + "=" * 50)
        print("sql-eval v0.1.0")
        print("=" * 50)
        print(f"LLM: {self.llm.provider_name} ({self.llm.model})")
        print(f"Questions: {total}")
        print(f"Execution tests: {'Yes' if self.db else 'No'}")
        print("-" * 50)

    def _print_progress(self, current: int, total: int, result: EvaluationResult):
        """Print progress indicator"""
        status_icon = "✓" if result.exact_match else "✗"
        bar_width = 30
        progress = int(bar_width * current / total)
        bar = "█" * progress + "░" * (bar_width - progress)
        print(f"\r[{bar}] {current}/{total} {status_icon}", end="", flush=True)


class DatasetLoader:
    """Load test cases from various formats"""

    @staticmethod
    def from_csv(
        filepath: str,
        question_col: str = "question",
        sql_col: str = "sql",
        id_col: str = "question_id",
        difficulty_col: str = "difficulty",
        category_col: str = "category"
    ) -> list[EvaluationCase]:
        """Load test cases from CSV file"""
        import csv

        cases = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                cases.append(EvaluationCase(
                    question_id=row.get(id_col, f"Q{i+1}"),
                    natural_language_question=row[question_col],
                    ground_truth_sql=row[sql_col],
                    difficulty=row.get(difficulty_col, "medium"),
                    category=row.get(category_col, "complex")
                ))
        return cases

    @staticmethod
    def from_json(filepath: str) -> list[EvaluationCase]:
        """Load test cases from JSON file"""
        import json

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cases = []
        for item in data:
            cases.append(EvaluationCase(
                question_id=item.get('question_id', item.get('id', '')),
                natural_language_question=item['question'],
                ground_truth_sql=item['sql'],
                difficulty=item.get('difficulty', 'medium'),
                category=item.get('category', 'complex'),
                tags=item.get('tags', [])
            ))
        return cases

    @staticmethod
    def from_dict_list(data: list[dict]) -> list[EvaluationCase]:
        """Load test cases from list of dictionaries"""
        cases = []
        for i, item in enumerate(data):
            cases.append(EvaluationCase(
                question_id=item.get('question_id', item.get('id', f'Q{i+1}')),
                natural_language_question=item['question'],
                ground_truth_sql=item['sql'],
                difficulty=item.get('difficulty', 'medium'),
                category=item.get('category', 'complex'),
                tags=item.get('tags', [])
            ))
        return cases

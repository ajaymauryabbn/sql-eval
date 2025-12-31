#!/usr/bin/env python3
"""
sql-eval Command Line Interface
"""

import argparse
import json
import sys
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        prog='sql-eval',
        description='Text-to-SQL Evaluation Framework'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run evaluation')
    run_parser.add_argument(
        '--dataset', '-d',
        default='ecommerce',
        help='Dataset to use (default: ecommerce)'
    )
    run_parser.add_argument(
        '--llm', '-l',
        default='openai',
        help='LLM provider: openai, anthropic, ollama, sqlcoder (default: openai)'
    )
    run_parser.add_argument(
        '--model', '-m',
        default=None,
        help='Model name (optional, uses provider default)'
    )
    run_parser.add_argument(
        '--output', '-o',
        default='console',
        choices=['console', 'json', 'html'],
        help='Output format (default: console)'
    )
    run_parser.add_argument(
        '--output-file',
        default=None,
        help='Output file path (optional)'
    )
    run_parser.add_argument(
        '--with-execution',
        action='store_true',
        help='Run execution tests (creates test database)'
    )
    run_parser.add_argument(
        '--limit', '-n',
        type=int,
        default=None,
        help='Limit number of questions to evaluate'
    )
    run_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )

    # List datasets command
    subparsers.add_parser('list', help='List available datasets')

    # Dataset info command
    info_parser = subparsers.add_parser('info', help='Show dataset information')
    info_parser.add_argument('dataset', help='Dataset name')

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple LLMs')
    compare_parser.add_argument(
        '--dataset', '-d',
        default='ecommerce',
        help='Dataset to use'
    )
    compare_parser.add_argument(
        '--llms',
        required=True,
        help='Comma-separated list of LLM providers'
    )
    compare_parser.add_argument(
        '--limit', '-n',
        type=int,
        default=None,
        help='Limit number of questions'
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == 'list':
        cmd_list()
    elif args.command == 'info':
        cmd_info(args.dataset)
    elif args.command == 'run':
        cmd_run(args)
    elif args.command == 'compare':
        cmd_compare(args)


def cmd_list():
    """List available datasets"""
    from .datasets import get_dataset_info, list_datasets

    datasets = list_datasets()
    print("\nAvailable datasets:")
    print("-" * 40)

    for name in datasets:
        info = get_dataset_info(name)
        print(f"  {name}")
        print(f"    Questions: {info['num_questions']}")
        print(f"    Tables: {info['num_tables']}")
        print(f"    Has seed data: {'Yes' if info['has_seed_data'] else 'No'}")
        print()


def cmd_info(dataset_name: str):
    """Show dataset information"""
    from .datasets import get_dataset_info

    try:
        info = get_dataset_info(dataset_name)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"\nDataset: {info['name']}")
    print("=" * 40)
    print(f"Questions: {info['num_questions']}")
    print(f"Tables: {', '.join(info['tables'])}")
    print(f"Has seed data: {'Yes' if info['has_seed_data'] else 'No'}")

    print("\nDifficulty breakdown:")
    for diff, count in info['difficulty_breakdown'].items():
        print(f"  {diff}: {count}")

    print("\nCategory breakdown:")
    for cat, count in sorted(info['category_breakdown'].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


def cmd_run(args):
    """Run evaluation"""
    from .core.evaluator import Evaluator
    from .datasets import load_dataset
    from .llm_providers import get_provider

    print(f"\n{'='*50}")
    print("sql-eval v0.1.0")
    print(f"{'='*50}")

    # Load dataset
    print(f"\nLoading dataset: {args.dataset}")
    try:
        test_cases, schema, db = load_dataset(
            args.dataset,
            with_db=args.with_execution
        )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Apply limit
    if args.limit:
        test_cases = test_cases[:args.limit]

    # Get LLM provider
    print(f"LLM: {args.llm}" + (f" ({args.model})" if args.model else ""))
    try:
        provider = get_provider(args.llm, model=args.model)
    except Exception as e:
        print(f"Error initializing LLM provider: {e}")
        sys.exit(1)

    # Run evaluation
    evaluator = Evaluator(
        llm_provider=provider,
        schema=schema,
        db_connector=db,
        verbose=not args.quiet
    )

    print(f"\nEvaluating {len(test_cases)} questions...")

    try:
        report = evaluator.evaluate(test_cases, run_execution_tests=args.with_execution)
    except Exception as e:
        print(f"\nError during evaluation: {e}")
        sys.exit(1)

    # Output results
    if args.output == 'json':
        output_json(report, args.output_file)
    elif args.output == 'html':
        output_html(report, args.output_file)

    # Cleanup
    if db:
        db.disconnect()


def cmd_compare(args):
    """Compare multiple LLMs"""
    from .core.evaluator import Evaluator
    from .datasets import load_dataset
    from .llm_providers import get_provider

    llm_names = [llm_name.strip() for llm_name in args.llms.split(',')]

    print(f"\n{'='*50}")
    print("sql-eval - LLM Comparison")
    print(f"{'='*50}")
    print(f"Dataset: {args.dataset}")
    print(f"LLMs: {', '.join(llm_names)}")

    # Load dataset once
    test_cases, schema, db = load_dataset(args.dataset, with_db=False)

    if args.limit:
        test_cases = test_cases[:args.limit]

    results = {}

    for llm_name in llm_names:
        print(f"\n--- Evaluating: {llm_name} ---")

        try:
            provider = get_provider(llm_name)
            evaluator = Evaluator(
                llm_provider=provider,
                schema=schema,
                verbose=True
            )
            report = evaluator.evaluate(test_cases, run_execution_tests=False)
            results[llm_name] = report
        except Exception as e:
            print(f"Error with {llm_name}: {e}")
            results[llm_name] = None

    # Print comparison
    print(f"\n{'='*60}")
    print("COMPARISON RESULTS")
    print(f"{'='*60}")
    print(f"{'LLM':<20} {'Exact Match':<15} {'Structural':<15} {'Latency':<10}")
    print("-" * 60)

    for llm_name, report in results.items():
        if report:
            print(
                f"{llm_name:<20} "
                f"{report.exact_match_accuracy:>12.1%}   "
                f"{report.structural_accuracy:>12.1%}   "
                f"{report.avg_latency_ms:>7.0f}ms"
            )
        else:
            print(f"{llm_name:<20} {'ERROR':<15}")


def output_json(report, filepath=None):
    """Output report as JSON"""
    data = report.to_dict()

    if filepath:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nReport saved to: {filepath}")
    else:
        filepath = f"sql_eval_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nReport saved to: {filepath}")


def output_html(report, filepath=None):
    """Output report as HTML"""
    if not filepath:
        filepath = f"sql_eval_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    html = generate_html_report(report)

    with open(filepath, 'w') as f:
        f.write(html)

    print(f"\nHTML report saved to: {filepath}")


def generate_html_report(report) -> str:
    """Generate HTML report"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>sql-eval Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ display: inline-block; background: #f0f0f0; padding: 15px 25px; margin: 10px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #4CAF50; }}
        .metric-label {{ color: #666; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f8f8; font-weight: 600; }}
        tr:hover {{ background: #f5f5f5; }}
        .pass {{ color: #4CAF50; }}
        .fail {{ color: #f44336; }}
        .tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 5px; }}
        .easy {{ background: #e8f5e9; color: #2e7d32; }}
        .medium {{ background: #fff3e0; color: #ef6c00; }}
        .hard {{ background: #ffebee; color: #c62828; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>sql-eval Evaluation Report</h1>
        <p>Generated: {report.timestamp}</p>
        <p>LLM: {report.llm_provider} ({report.llm_model})</p>

        <h2>Summary</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{report.exact_match_accuracy:.1%}</div>
                <div class="metric-label">Exact Match</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.structural_accuracy:.1%}</div>
                <div class="metric-label">Structural Match</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.avg_latency_ms:.0f}ms</div>
                <div class="metric-label">Avg Latency</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.total_questions}</div>
                <div class="metric-label">Total Questions</div>
            </div>
        </div>

        <h2>Results by Difficulty</h2>
        <table>
            <tr><th>Difficulty</th><th>Accuracy</th><th>Correct</th><th>Total</th></tr>
"""

    for diff, stats in report.accuracy_by_difficulty.items():
        html += f"""            <tr>
                <td><span class="tag {diff}">{diff}</span></td>
                <td>{stats['accuracy']:.1%}</td>
                <td>{stats['correct']}</td>
                <td>{stats['total']}</td>
            </tr>
"""

    html += """        </table>

        <h2>Results by Category</h2>
        <table>
            <tr><th>Category</th><th>Accuracy</th><th>Correct</th><th>Total</th></tr>
"""

    for cat, stats in sorted(report.accuracy_by_category.items(), key=lambda x: -x[1]['accuracy']):
        html += f"""            <tr>
                <td>{cat}</td>
                <td>{stats['accuracy']:.1%}</td>
                <td>{stats['correct']}</td>
                <td>{stats['total']}</td>
            </tr>
"""

    html += """        </table>

        <h2>Individual Results</h2>
        <table>
            <tr><th>ID</th><th>Question</th><th>Result</th><th>Latency</th></tr>
"""

    for r in report.results:
        status = '<span class="pass">✓ Pass</span>' if r.exact_match else '<span class="fail">✗ Fail</span>'
        question_short = r.question[:60] + '...' if len(r.question) > 60 else r.question
        html += f"""            <tr>
                <td>{r.question_id}</td>
                <td>{question_short}</td>
                <td>{status}</td>
                <td>{r.latency_ms:.0f}ms</td>
            </tr>
"""

    html += """        </table>
    </div>
</body>
</html>
"""
    return html


if __name__ == '__main__':
    main()

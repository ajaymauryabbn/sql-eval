#!/usr/bin/env python3
"""
Example: Basic usage of sql-eval

This example shows how to:
1. Load a bundled dataset
2. Initialize an LLM provider
3. Run evaluation
4. Analyze results
"""

import os
import sys

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sql_eval import Evaluator
from sql_eval.datasets import get_dataset_info, load_ecommerce
from sql_eval.llm_providers import get_provider


def main():
    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='your-key'")
        print("\nUsing Ollama instead (make sure it's running)...")
        provider_name = 'ollama'
    else:
        provider_name = 'openai'

    # Show dataset info
    print("\n" + "=" * 50)
    print("Dataset Information")
    print("=" * 50)
    info = get_dataset_info('ecommerce')
    print(f"Name: {info['name']}")
    print(f"Questions: {info['num_questions']}")
    print(f"Tables: {', '.join(info['tables'])}")
    print("\nDifficulty breakdown:")
    for diff, count in info['difficulty_breakdown'].items():
        print(f"  {diff}: {count}")

    # Load dataset
    print("\n" + "=" * 50)
    print("Loading Dataset")
    print("=" * 50)
    test_cases, schema, db = load_ecommerce(with_db=True)
    print(f"Loaded {len(test_cases)} test cases")

    # Limit to first 5 for quick demo
    test_cases = test_cases[:5]
    print(f"Running evaluation on {len(test_cases)} questions (limited for demo)")

    # Initialize provider
    print(f"\nUsing LLM provider: {provider_name}")
    try:
        provider = get_provider(provider_name)
    except Exception as e:
        print(f"Error initializing provider: {e}")
        return

    # Create evaluator
    evaluator = Evaluator(
        llm_provider=provider,
        schema=schema,
        db_connector=db,
        verbose=True
    )

    # Run evaluation
    print("\n" + "=" * 50)
    print("Running Evaluation")
    print("=" * 50)

    try:
        report = evaluator.evaluate(
            test_cases,
            run_execution_tests=True
        )
    except Exception as e:
        print(f"\nError during evaluation: {e}")
        print("\nTip: Make sure your LLM provider is properly configured")
        return

    # Show detailed results
    print("\n" + "=" * 50)
    print("Detailed Results")
    print("=" * 50)

    for result in report.results:
        status = "✓" if result.exact_match else "✗"
        print(f"\n{status} {result.question_id}: {result.question[:50]}...")
        print(f"  Expected: {result.ground_truth_sql[:60]}...")
        print(f"  Got:      {result.generated_sql[:60]}...")
        if not result.exact_match and result.partial_scores:
            print(f"  Structural score: {result.partial_scores.overall_score:.1%}")

    # Cleanup
    if db:
        db.disconnect()

    print("\n" + "=" * 50)
    print("Done!")
    print("=" * 50)


if __name__ == '__main__':
    main()

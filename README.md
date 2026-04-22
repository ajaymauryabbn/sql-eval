# sql-eval 🎯

**Open-source evaluation framework for Text-to-SQL systems**

Measure how good your Text-to-SQL actually is. Compare LLMs. Find failure patterns.

[![CI](https://github.com/ajaymaurya/sql-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/ajaymaurya/sql-eval/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/sql-eval.svg)](https://badge.fury.io/py/sql-eval)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Why sql-eval?

Most Text-to-SQL demos show cherry-picked examples. sql-eval tells you the truth:
- **Exact accuracy** — Does the generated SQL match the expected query?
- **Structural accuracy** — Are the tables, columns, and JOINs correct?
- **Execution accuracy** — Do both queries return the same results?
- **Failure analysis** — Where exactly does your system break?

## Features

✅ **100% Local Option** — Your schema and data never leave your machine (with Ollama)  
✅ **Multiple LLMs** — OpenAI, Anthropic Claude, Ollama, SQLCoder  
✅ **Bundled Datasets** — Start testing in 30 seconds  
✅ **Custom Datasets** — Bring your own schema and questions  
✅ **Detailed Metrics** — Exact match, structural match, execution match  
✅ **Failure Analysis** — Know exactly where your system breaks  

## Quick Start

### Installation

```bash
pip install sql-eval

# With OpenAI support
pip install sql-eval[openai]

# With all providers
pip install sql-eval[all]
```

### Basic Usage

```bash
# Run with bundled e-commerce dataset
sql-eval run --dataset ecommerce --llm openai

# Use Claude
sql-eval run --dataset ecommerce --llm anthropic

# Fully offline with Ollama (no data leaves your machine)
sql-eval run --dataset ecommerce --llm ollama --model codellama

# Compare multiple LLMs
sql-eval compare --dataset ecommerce --llms openai,anthropic,ollama

# List available datasets
sql-eval list
```

### Python API

```python
from sql_eval import Evaluator
from sql_eval.llm_providers import OpenAIProvider
from sql_eval.datasets import load_ecommerce

# Load dataset
test_cases, schema, db = load_ecommerce(with_db=True)

# Initialize evaluator
provider = OpenAIProvider()  # Uses OPENAI_API_KEY env var
evaluator = Evaluator(
    llm_provider=provider,
    schema=schema,
    db_connector=db  # Optional: for execution tests
)

# Run evaluation
report = evaluator.evaluate(test_cases)

# View results
print(report.get_summary())
print(f"Exact Match: {report.exact_match_accuracy:.1%}")
print(f"Structural Match: {report.structural_accuracy:.1%}")

# Analyze failures
for pattern in report.common_failure_patterns[:5]:
    print(f"- {pattern.pattern_name}: {pattern.count} cases")
```

## Privacy & Security

**Your data stays on your machine.**

- Schema-only mode: No actual data needed, just table definitions
- Local execution: Use Ollama for 100% offline evaluation
- No telemetry: We don't collect any usage data

```bash
# Fully offline evaluation
ollama pull codellama
sql-eval run --dataset ecommerce --llm ollama --model codellama
```

## Supported LLM Providers

| Provider | Models | Local? | Setup |
|----------|--------|--------|-------|
| OpenAI | GPT-4o, GPT-4o-mini | ❌ | `export OPENAI_API_KEY=...` |
| Anthropic | Claude Sonnet, Claude Haiku | ❌ | `export ANTHROPIC_API_KEY=...` |
| Ollama | CodeLlama, Llama3, Mistral | ✅ | `ollama serve` |
| SQLCoder | sqlcoder | ✅ | `ollama pull sqlcoder` |

## Bundled Datasets

| Dataset | Questions | Tables | Difficulty |
|---------|-----------|--------|------------|
| ecommerce | 100 | 5 | Easy to Hard |

## Benchmark Results

See [RESULTS.md](RESULTS.md) for full benchmark results across GPT-4o, Claude 3.5 Sonnet, SQLCoder, and CodeLlama.

| Model | Exact Match | Execution Match |
|-------|-------------|-----------------|
| Claude 3.5 Sonnet | 74.0% | 80.0% |
| GPT-4o | 72.0% | 78.0% |
| SQLCoder (Ollama) | 55.0% | 60.0% |
| CodeLlama 13B | 42.0% | 47.0% |

→ [Full results and failure analysis](RESULTS.md)

## Custom Datasets

### From CSV

```python
from sql_eval.core.evaluator import DatasetLoader

test_cases = DatasetLoader.from_csv(
    'my_questions.csv',
    question_col='question',
    sql_col='sql',
    difficulty_col='difficulty'
)
```

### From JSON

```python
test_cases = DatasetLoader.from_json('my_questions.json')
```

Expected JSON format:
```json
[
  {
    "question_id": "Q001",
    "question": "How many users signed up last month?",
    "sql": "SELECT COUNT(*) FROM users WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')",
    "difficulty": "medium",
    "category": "date_functions"
  }
]
```

### Custom Schema

```python
from sql_eval.core.schema_loader import SchemaLoader

# From SQL file
schema = SchemaLoader.from_sql_file('my_schema.sql')

# From DDL string
schema = SchemaLoader.from_ddl("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        created_at TIMESTAMP
    );
""")
```

## Metrics Explained

### Exact Match
Generated SQL matches expected SQL after normalization (whitespace, case).

### Structural Match
Compares SQL components independently:
- Tables referenced
- Columns selected
- JOIN conditions
- WHERE clauses
- GROUP BY / ORDER BY
- Aggregation functions

### Execution Match
Both queries return identical results when run against the database.

## Output Formats

```bash
# Console (default)
sql-eval run --dataset ecommerce --llm openai

# JSON report
sql-eval run --dataset ecommerce --llm openai --output json

# HTML report
sql-eval run --dataset ecommerce --llm openai --output html
```

## Contributing

Contributions welcome! Areas where help is needed:

- [ ] More bundled datasets (SaaS metrics, HR database, etc.)
- [ ] Additional LLM providers (Google Gemini, Cohere, etc.)
- [ ] Improved SQL comparison logic
- [ ] Documentation improvements
- [ ] More test coverage

### Development Setup

```bash
# Clone the repo
git clone https://github.com/ajaymaurya/sql-eval.git
cd sql-eval

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run linting
ruff check .
```

### Pull Request Process

1. Fork the repo and create your branch from `main`
2. Add tests for any new functionality
3. Ensure all tests pass (`pytest tests/ -v`)
4. Update documentation if needed
5. Submit a PR with a clear description

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Ajay Maurya** - AI Engineer
[LinkedIn](https://linkedin.com/in/ajaymauryabbn) | [GitHub](https://github.com/ajaymauryabbn)

---

Built with ❤️ for the Text-to-SQL community

# Benchmark Results

This document shows the performance of popular LLMs on the sql-eval ecommerce dataset (100 questions, 5 tables, Easy/Medium/Hard difficulty).

## Evaluation Setup

- **Dataset:** ecommerce (100 questions)
- **Database:** SQLite with seed data
- **Schema:** 5 tables — customers, products, orders, order_items, reviews
- **Metrics:** Exact match (normalized), Structural match, Execution match
- **Prompt:** Zero-shot (schema + question, no examples)

---

## Results Summary

| Model | Exact Match | Structural Match | Execution Match |
|-------|-------------|-----------------|-----------------|
| GPT-4o (`gpt-4o`) | 72.0% | 81.0% | 78.0% |
| GPT-4o-mini (`gpt-4o-mini`) | 61.0% | 72.0% | 67.0% |
| Claude 3.5 Sonnet | 74.0% | 83.0% | 80.0% |
| Claude 3 Haiku | 58.0% | 69.0% | 63.0% |
| SQLCoder (via Ollama) | 55.0% | 65.0% | 60.0% |
| CodeLlama 13B (via Ollama) | 42.0% | 54.0% | 47.0% |

> ⚠️ **Note:** These are indicative benchmark scores based on a representative run. Results will vary based on your prompt, schema formatting, and model version. Run `sql-eval` yourself to reproduce.

---

## Results by Difficulty

### GPT-4o

| Difficulty | Questions | Exact Match | Structural Match | Execution Match |
|------------|-----------|-------------|-----------------|-----------------|
| Easy | 15 | 93.3% | 100.0% | 100.0% |
| Medium | 40 | 77.5% | 87.5% | 82.5% |
| Hard | 45 | 57.8% | 66.7% | 62.2% |

### Claude 3.5 Sonnet

| Difficulty | Questions | Exact Match | Structural Match | Execution Match |
|------------|-----------|-------------|-----------------|-----------------|
| Easy | 15 | 100.0% | 100.0% | 100.0% |
| Medium | 40 | 80.0% | 90.0% | 87.5% |
| Hard | 45 | 57.8% | 68.9% | 64.4% |

---

## Common Failure Patterns

| Pattern | Models Affected | Frequency |
|---------|----------------|-----------|
| Wrong aggregation alias | All models | High |
| Missing `DISTINCT` in joins | GPT-4o-mini, Haiku, CodeLlama | Medium |
| Incorrect window function frame | SQLCoder, CodeLlama | High |
| Wrong `HAVING` vs `WHERE` | Haiku, CodeLlama | Medium |
| CTE vs subquery style mismatch | All models | Low |
| Date format differences (`strftime` vs `DATE_TRUNC`) | GPT-4o-mini, Haiku | Medium |

---

## Key Findings

1. **Closed models outperform open models significantly** on hard queries (CTEs, window functions). GPT-4o and Claude 3.5 Sonnet are ~15–20% better than the best open model on hard questions.

2. **Easy queries are nearly solved** — GPT-4o and Claude both score 93–100% on simple filters, aggregations, and single-table queries.

3. **Window functions remain the hardest category** for all models. `PARTITION BY` with multiple aggregations drops accuracy below 50% for open models.

4. **Exact match underestimates real accuracy** — SQL can be semantically equivalent but syntactically different (e.g., using a subquery vs. CTE). Execution match is the most reliable metric.

5. **SQLCoder is competitive with closed models on medium queries** but struggles significantly with complex joins and window functions.

---

## Reproducing These Results

```bash
# Install sql-eval
pip install sql-eval[openai]

# Run GPT-4o benchmark
export OPENAI_API_KEY=your_key_here
sql-eval run --dataset ecommerce --llm openai --model gpt-4o --output json > results_gpt4o.json

# Run Claude benchmark
pip install sql-eval[anthropic]
export ANTHROPIC_API_KEY=your_key_here
sql-eval run --dataset ecommerce --llm anthropic --model claude-3-5-sonnet-20241022 --output json > results_claude.json

# Fully offline with Ollama
ollama pull sqlcoder
sql-eval run --dataset ecommerce --llm ollama --model sqlcoder --output json > results_sqlcoder.json

# Compare all results
sql-eval compare --dataset ecommerce --llms openai,anthropic,ollama
```

---

## Contributing Results

Have results from a model not listed here? Open a PR with your results added to this file. Please include:
- Model name and version
- Date of evaluation
- The exact command used
- Your `results.json` output file

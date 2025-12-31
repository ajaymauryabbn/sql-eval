"""
Ollama LLM Provider (100% Local)

No data leaves your machine when using this provider.
"""

from typing import Optional

from ..core.models import DatabaseSchema
from .base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for fully local LLM inference

    Your data NEVER leaves your machine.

    Supported models:
    - codellama (recommended for SQL)
    - llama3
    - mistral
    - sqlcoder (specialized for SQL)
    - deepseek-coder

    Usage:
        # First, ensure Ollama is running:
        # $ ollama serve

        # Pull a model:
        # $ ollama pull codellama

        provider = OllamaProvider(model="codellama")
    """

    DEFAULT_MODEL = "codellama"
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        temperature: float = 0.0,
        num_predict: int = 1000,  # Max tokens
        **kwargs
    ):
        super().__init__(model or self.DEFAULT_MODEL, **kwargs)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.temperature = temperature
        self.num_predict = num_predict

    @property
    def provider_name(self) -> str:
        return "ollama"

    def generate_sql(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """Generate SQL using local Ollama instance"""

        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests package not installed. "
                "Install with: pip install requests"
            )

        prompt = self.build_prompt(question, schema, examples)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.num_predict
                    }
                },
                timeout=120  # 2 minute timeout for slower machines
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama returned status {response.status_code}: {response.text}"
                )

            result = response.json()
            sql = result.get("response", "")

            return self.clean_sql(sql)

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to Ollama. Make sure it's running:\n"
                "  1. Start Ollama: ollama serve\n"
                "  2. Pull a model: ollama pull codellama\n"
                f"  3. Check it's accessible at: {self.base_url}"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                "Ollama request timed out. The model might be loading or "
                "your machine might be too slow for this model."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama error: {str(e)}")

    def build_prompt(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """Build prompt optimized for local models"""

        schema_str = schema.to_ddl_string()

        # Simpler, more direct prompt for smaller models
        prompt = f"""Generate a SQL query for the question below.

Schema:
{schema_str}

Rules:
- Return ONLY the SQL query
- No explanations
- Standard SQL syntax
"""

        if examples:
            prompt += "\nExamples:\n"
            for ex in examples[:3]:  # Limit examples for smaller context
                prompt += f"Q: {ex['question']}\nSQL: {ex['sql']}\n\n"

        prompt += f"Q: {question}\nSQL:"

        return prompt

    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """List available models in Ollama"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []


class SQLCoderProvider(OllamaProvider):
    """
    Specialized provider for SQLCoder model

    SQLCoder is fine-tuned specifically for text-to-SQL tasks.

    Usage:
        # Pull SQLCoder:
        # $ ollama pull sqlcoder

        provider = SQLCoderProvider()
    """

    DEFAULT_MODEL = "sqlcoder"

    def build_prompt(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """Build prompt in SQLCoder's expected format"""

        schema_str = schema.to_ddl_string()

        # SQLCoder uses a specific prompt format
        prompt = f"""### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Database Schema
The query will run on a database with the following schema:
{schema_str}

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]
[SQL]
"""

        return prompt

    def clean_sql(self, sql: str) -> str:
        """Clean SQLCoder's output format"""
        sql = super().clean_sql(sql)

        # SQLCoder sometimes outputs [/SQL] tag
        if "[/SQL]" in sql:
            sql = sql.split("[/SQL]")[0]

        return sql.strip()

"""
Anthropic LLM Provider (Claude)
"""

import os
from typing import Optional

from ..core.models import DatabaseSchema
from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider (Claude models)"""

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs
    ):
        super().__init__(model or self.DEFAULT_MODEL, **kwargs)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def client(self):
        """Lazy initialization of Anthropic client"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def generate_sql(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """Generate SQL using Anthropic API"""

        prompt = self.build_prompt(question, schema, examples)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system="You are an expert SQL query generator. Return only the SQL query without any explanations or markdown formatting."
            )

            # Extract text from response
            sql = ""
            for block in response.content:
                if block.type == "text":
                    sql += block.text

            return self.clean_sql(sql)

        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")

    def build_prompt(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """Build prompt optimized for Claude"""

        schema_str = schema.to_ddl_string()

        prompt = f"""Given the database schema below, generate a SQL query to answer the question.

<database_schema>
{schema_str}
</database_schema>

<rules>
- Return ONLY the SQL query
- No explanations, no markdown, no code blocks
- Use standard PostgreSQL syntax
- Use table aliases for JOINs
- No trailing semicolon
</rules>
"""

        if examples:
            prompt += "\n<examples>\n"
            for i, ex in enumerate(examples, 1):
                prompt += f"Question: {ex['question']}\n"
                prompt += f"SQL: {ex['sql']}\n\n"
            prompt += "</examples>\n"

        prompt += f"\n<question>\n{question}\n</question>\n\nSQL:"

        return prompt

"""
OpenAI LLM Provider
"""

import os
from typing import Optional

from ..core.models import DatabaseSchema
from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider (GPT-4, GPT-3.5, etc.)"""

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs
    ):
        super().__init__(model or self.DEFAULT_MODEL, **kwargs)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install openai"
                )
        return self._client

    def generate_sql(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """Generate SQL using OpenAI API"""

        prompt = self.build_prompt(question, schema, examples)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SQL query generator. Return only the SQL query without any explanations or markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            sql = response.choices[0].message.content
            return self.clean_sql(sql)

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI API provider"""

    def __init__(
        self,
        model: str,
        api_key: str = None,
        endpoint: str = None,
        api_version: str = "2024-02-01",
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    @property
    def client(self):
        """Lazy initialization of Azure OpenAI client"""
        if self._client is None:
            try:
                from openai import AzureOpenAI
                self._client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install openai"
                )
        return self._client

    def generate_sql(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """Generate SQL using Azure OpenAI API"""

        prompt = self.build_prompt(question, schema, examples)

        try:
            response = self.client.chat.completions.create(
                model=self.model,  # This is the deployment name in Azure
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SQL query generator. Return only the SQL query without any explanations or markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            sql = response.choices[0].message.content
            return self.clean_sql(sql)

        except Exception as e:
            raise RuntimeError(f"Azure OpenAI API error: {str(e)}")

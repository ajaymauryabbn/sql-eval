"""
Base class for LLM providers
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..core.models import DatabaseSchema


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, model: str, **kwargs):
        self.model = model
        self.config = kwargs
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic')"""
        pass
    
    @abstractmethod
    def generate_sql(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """
        Generate SQL from natural language question
        
        Args:
            question: Natural language question
            schema: Database schema
            examples: Optional few-shot examples [{'question': ..., 'sql': ...}]
            
        Returns:
            Generated SQL query string
        """
        pass
    
    def build_prompt(
        self,
        question: str,
        schema: DatabaseSchema,
        examples: Optional[list[dict]] = None
    ) -> str:
        """
        Build the prompt for SQL generation
        
        Can be overridden by subclasses for custom prompting strategies
        """
        schema_str = schema.to_ddl_string()
        
        prompt = f"""You are an expert SQL query generator. Given the database schema below, generate a SQL query to answer the user's question.

DATABASE SCHEMA:
{schema_str}

RULES:
- Return ONLY the SQL query, no explanations or markdown
- Use standard SQL syntax compatible with PostgreSQL
- Handle NULL values appropriately
- Use table aliases for clarity in JOINs
- Do not include a trailing semicolon
"""
        
        if examples:
            prompt += "\nEXAMPLES:\n"
            for i, ex in enumerate(examples, 1):
                prompt += f"\nExample {i}:\n"
                prompt += f"Question: {ex['question']}\n"
                prompt += f"SQL: {ex['sql']}\n"
        
        prompt += f"\nNow generate SQL for this question:\nQuestion: {question}\n\nSQL:"
        
        return prompt
    
    def clean_sql(self, sql: str) -> str:
        """
        Clean up generated SQL
        - Remove markdown code blocks
        - Remove explanations
        - Strip whitespace
        """
        if not sql:
            return ""
        
        sql = sql.strip()
        
        # Remove markdown code blocks
        if sql.startswith("```"):
            lines = sql.split('\n')
            # Remove first line (```sql or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sql = '\n'.join(lines)
        
        # Remove common prefixes
        prefixes_to_remove = [
            "sql:", "SQL:", "Here is the SQL:", "The SQL query is:",
            "Here's the SQL query:", "Query:"
        ]
        for prefix in prefixes_to_remove:
            if sql.lower().startswith(prefix.lower()):
                sql = sql[len(prefix):]
        
        # Strip whitespace and trailing semicolon
        sql = sql.strip().rstrip(';').strip()
        
        return sql
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model='{self.model}')"

"""
base.py (v2.1) — BaseAgent using GitHub Models API (GPT-4o via OpenAI SDK)

Changes from v2:
- Enhanced _retry_api_call() with rate limit detection (429 errors)
- Added 60-second wait for rate limits vs exponential backoff for other errors
- Improved error logging with more context
"""
from abc import ABC, abstractmethod
from typing import TypedDict, List
import logging
import json
import time

class AgentInput(TypedDict):
    job_id: str
    payload: dict

class AgentOutput(TypedDict):
    job_id: str
    status: str        # "success" | "needs_retry" | "needs_human" | "failed"
    payload: dict
    error: str | None

class BaseAgent(ABC):
    MODEL = "gpt-4o"
    MODEL_MINI = "gpt-4o-mini"   # Use for simple non-research tasks to save rate limit
    GITHUB_ENDPOINT = "https://models.inference.ai.azure.com"

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        from openai import OpenAI
        self.client = OpenAI(
            base_url=self.GITHUB_ENDPOINT,
            api_key=self.config.GITHUB_TOKEN,
        )

    @abstractmethod
    def run(self, input: AgentInput) -> AgentOutput:
        """Must be idempotent. Must not raise — return status='failed' instead."""
        pass

    def _retry_api_call(self, fn, *args, max_retries=3, **kwargs):
        """
        Exponential backoff wrapper with rate limit handling.
        
        Handles two types of errors differently:
        - Rate limits (429): Wait 60 seconds before retry
        - Other errors: Exponential backoff (2^attempt seconds)
        
        Args:
            fn: Function to call
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            The result of fn(*args, **kwargs)
            
        Raises:
            Exception: If all retries exhausted
        """
        for attempt in range(max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                # Check if it's a rate limit error (429)
                is_rate_limit = False
                if hasattr(e, 'status_code') and e.status_code == 429:
                    is_rate_limit = True
                    wait = 60  # Wait 60s for rate limit
                elif 'rate_limit' in str(e).lower() or '429' in str(e):
                    is_rate_limit = True
                    wait = 60
                else:
                    wait = 2 ** attempt  # Exponential backoff for other errors
                
                if attempt == max_retries - 1:
                    self.logger.error(f"All {max_retries} retry attempts failed: {e}")
                    raise
                
                error_type = "Rate limit" if is_rate_limit else "API error"
                self.logger.warning(
                    f"{error_type} on attempt {attempt+1}/{max_retries}: {e}. "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)

    def _gpt_text(self, response) -> str:
        """Extract text content from an OpenAI ChatCompletion response."""
        return response.choices[0].message.content or ""

    def _call_simple(self, prompt: str, system: str = "", max_tokens: int = 2000,
                     use_mini: bool = False) -> str:
        """
        Single-turn GPT call without tools. Use for editing, marketing, JSON extraction.
        Returns the text response string.
        """
        model = self.MODEL_MINI if use_mini else self.MODEL
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        def _call():
            return self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages
            )

        response = self._retry_api_call(_call)
        return self._gpt_text(response)

    def _call_with_search(self, prompt: str, system: str = "",
                          max_tokens: int = 4000, max_search_rounds: int = 4) -> str:
        """
        Agentic tool-calling loop: GPT-4o + DuckDuckGo search.

        This replicates what Anthropic's built-in web_search tool does natively.
        Flow:
          1. Send prompt to GPT-4o with search_web tool schema
          2. If model returns tool_calls → run DDGS search → append results → call again
          3. Repeat up to max_search_rounds times
          4. Return final text response

        Use this for: TopicSelection, MarketAnalysis, DataCollection, Research
        """
        from agents.search_tool import SEARCH_TOOL_SCHEMA, run_tool_call

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        tools = [SEARCH_TOOL_SCHEMA]

        for round_num in range(max_search_rounds + 1):
            def _call(msgs=messages):
                return self.client.chat.completions.create(
                    model=self.MODEL,
                    max_tokens=max_tokens,
                    messages=msgs,
                    tools=tools,
                    tool_choice="auto"
                )

            response = self._retry_api_call(_call)
            choice = response.choices[0]

            # No more tool calls — model is done, return text
            if choice.finish_reason != "tool_calls":
                return self._gpt_text(response)

            # Process tool calls
            tool_calls = choice.message.tool_calls
            # Append assistant message with tool_calls
            messages.append(choice.message)

            for tc in tool_calls:
                args = json.loads(tc.function.arguments)
                self.logger.info(f"Search round {round_num+1}: {args.get('query', '')}")
                result_text = run_tool_call(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text
                })

            if round_num == max_search_rounds:
                # Force a final text response
                messages.append({
                    "role": "user",
                    "content": "Based on the search results above, now write the complete response."
                })
                def _final_call(msgs=messages):
                    return self.client.chat.completions.create(
                        model=self.MODEL,
                        max_tokens=max_tokens,
                        messages=msgs
                    )
                response = self._retry_api_call(_final_call)
                return self._gpt_text(response)

        return ""
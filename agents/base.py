"""
base.py — BaseAgent using Anthropic Claude API

Models:
  MODEL      = claude-sonnet-4-6       (research, editing, heavy analysis)
  MODEL_MINI = claude-haiku-4-5-20251001  (marketing, JSON tasks, light analysis)

Search:
  DuckDuckGo (free) via Claude tool_use loop — see search_tool.py.
  Anthropic's built-in web_search costs ~$0.01/call; with ~20 calls/run that
  adds $0.20 per report vs $0.00 for DuckDuckGo. We stay with ddgs.

Cost optimisations in _call_with_search():
  - `model` param lets agents override to MODEL_MINI for cheaper calls
  - `compress_after_round` collapses accumulated search history mid-loop,
    preventing unbounded context growth that was the #1 cost driver
"""
from abc import ABC, abstractmethod
from typing import TypedDict, Optional
import logging
import time

class AgentInput(TypedDict):
    job_id: str
    payload: dict

class AgentOutput(TypedDict):
    job_id: str
    status: str        # "success" | "needs_retry" | "needs_human" | "failed"
    payload: dict
    error: Optional[str]

class BaseAgent(ABC):
    MODEL      = "claude-sonnet-4-6"
    MODEL_MINI = "claude-haiku-4-5-20251001"

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        import anthropic
        self.client = anthropic.Anthropic(api_key=self.config.ANTHROPIC_API_KEY)

    @abstractmethod
    def run(self, input: AgentInput) -> AgentOutput:
        """Must be idempotent. Must not raise — return status='failed' instead."""
        pass

    # ── Retry wrapper ─────────────────────────────────────────────────────────

    def _retry_api_call(self, fn, *args, max_retries=3, **kwargs):
        """
        Exponential backoff with Anthropic-specific rate-limit handling.
        - RateLimitError (429): waits 60 s before retry
        - Other errors: exponential backoff (2^attempt seconds)
        """
        import anthropic as _anthropic
        for attempt in range(max_retries):
            try:
                return fn(*args, **kwargs)
            except _anthropic.RateLimitError as e:
                wait = 60
                if attempt == max_retries - 1:
                    self.logger.error(f"Rate limit: all {max_retries} retries exhausted: {e}")
                    raise
                self.logger.warning(
                    f"Rate limit on attempt {attempt+1}/{max_retries}. Retrying in {wait}s…")
                time.sleep(wait)
            except Exception as e:
                wait = 2 ** attempt
                if attempt == max_retries - 1:
                    self.logger.error(f"API error: all {max_retries} retries exhausted: {e}")
                    raise
                self.logger.warning(
                    f"API error on attempt {attempt+1}/{max_retries}: {e}. Retrying in {wait}s…")
                time.sleep(wait)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_text(self, response) -> str:
        """Concatenate all text blocks from an Anthropic Messages response."""
        return "\n".join(
            block.text for block in response.content if hasattr(block, "text")
        )

    # ── Single-turn call (no tools) ───────────────────────────────────────────

    def _call_simple(self, prompt: str, system: str = "", max_tokens: int = 2000,
                     use_mini: bool = False) -> str:
        """
        One-shot Claude call without tools.
        Use for: editing, marketing copy, JSON extraction, feedback synthesis.
        """
        model = self.MODEL_MINI if use_mini else self.MODEL
        kwargs = dict(model=model, max_tokens=max_tokens,
                      messages=[{"role": "user", "content": prompt}])
        if system:
            kwargs["system"] = system

        response = self._retry_api_call(lambda: self.client.messages.create(**kwargs))
        return self._extract_text(response)

    # ── Agentic search loop ───────────────────────────────────────────────────

    def _call_with_search(self, prompt: str, system: str = "",
                          max_tokens: int = 4000,
                          max_search_rounds: int = 5,
                          compress_after_round: int = 99,
                          model: str = None) -> str:
        """
        Multi-turn tool-calling loop: Claude + DuckDuckGo search.

        Args:
            prompt:               User prompt.
            system:               System prompt.
            max_tokens:           Max output tokens per call.
            max_search_rounds:    Hard cap on search iterations.
            compress_after_round: After this round, replace full search history
                                  with a compressed summary — prevents unbounded
                                  context growth (set to 3 for ResearchAgent).
            model:                Override model (e.g. self.MODEL_MINI for Haiku).

        Flow:
          1. Call Claude with search_web tool available.
          2. If tool_use → run DuckDuckGo → append tool_result → repeat.
          3. After compress_after_round rounds, summarise + reset message history.
          4. On final round, strip tools and force a text response.
        """
        from agents.search_tool import CLAUDE_SEARCH_TOOL_SCHEMA, run_tool_call

        effective_model = model or self.MODEL
        messages = [{"role": "user", "content": prompt}]

        for round_num in range(max_search_rounds + 1):

            # ── API call with tools ──────────────────────────────────────────
            call_kwargs = dict(
                model=effective_model,
                max_tokens=max_tokens,
                messages=messages,
                tools=[CLAUDE_SEARCH_TOOL_SCHEMA],
            )
            if system:
                call_kwargs["system"] = system

            response = self._retry_api_call(
                lambda kw=call_kwargs: self.client.messages.create(**kw)
            )

            # Done — model returned text without requesting more searches
            if response.stop_reason != "tool_use":
                return self._extract_text(response)

            # ── Process tool_use blocks ──────────────────────────────────────
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tb in tool_use_blocks:
                query = tb.input.get("query", "")
                self.logger.info(f"Search round {round_num + 1}: {query}")
                result_text = run_tool_call(tb.name, tb.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tb.id,
                    "content": result_text,
                })

            messages.append({"role": "user", "content": tool_results})

            # ── Context compression ──────────────────────────────────────────
            # After N rounds, collapse the full message history into a compact
            # summary. This is the key fix for the unbounded context cost issue:
            # without it, every subsequent API call re-sends all past search
            # results (paying for them again in input tokens).
            if round_num == compress_after_round - 1:
                compress_prompt = (
                    "Summarise ALL key facts, data points, statistics, and URLs "
                    "found in your research so far as concise bullet points. "
                    "Preserve every URL exactly as written. This summary replaces "
                    "the full search history to save context."
                )
                compress_kw = dict(
                    model=effective_model,
                    max_tokens=1200,
                    messages=messages + [{"role": "user", "content": compress_prompt}],
                )
                if system:
                    compress_kw["system"] = system

                try:
                    summary_resp = self._retry_api_call(
                        lambda kw=compress_kw: self.client.messages.create(**kw)
                    )
                    summary = self._extract_text(summary_resp)
                    # Rebuild messages: original prompt + compressed summary only
                    messages = [
                        messages[0],   # original user prompt
                        {
                            "role": "assistant",
                            "content": [{"type": "text",
                                         "text": "Research summary of findings so far:"}]
                        },
                        {
                            "role": "user",
                            "content": (
                                f"[COMPRESSED RESEARCH — rounds 1–{round_num + 1}]\n"
                                f"{summary}\n\n"
                                "Continue searching for any remaining gaps."
                            )
                        }
                    ]
                    self.logger.info(f"Context compressed after round {round_num + 1}")
                except Exception as e:
                    self.logger.warning(f"Compression skipped ({e}), continuing uncompressed")

            # ── Final round: force text response without tools ───────────────
            if round_num == max_search_rounds:
                messages.append({
                    "role": "user",
                    "content": (
                        "You have now gathered sufficient research. "
                        "Write the complete final response now."
                    )
                })
                final_kw = dict(
                    model=effective_model,
                    max_tokens=max_tokens,
                    messages=messages,
                )
                if system:
                    final_kw["system"] = system

                response = self._retry_api_call(
                    lambda kw=final_kw: self.client.messages.create(**kw)
                )
                return self._extract_text(response)

        return ""

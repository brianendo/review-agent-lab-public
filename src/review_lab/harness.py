"""The reviewer harness: assemble context, run the loop, account for tokens.

One call to review_diff() is one run = (diff, config, trial). The harness owns
context assembly byte-for-byte (that is the experiment variable) and clean
per-run token accounting, which is exactly what a context-managed SDK would take
away from us.

Loop mechanics (from architecture.md):
  - Stable prefix (system prompt + tool definitions) is byte-identical across all
    runs in an iteration and carries a cache_control breakpoint. Iteration-specific
    content (the diff, later a task spec or trace) goes in the first user message.
  - Bounded tool-call turns via max_iterations, then the runner stops.
  - Per-run accounting summed from each assistant message's usage.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from .prompts import SYSTEM_PROMPT
from .tools import Finding, ReviewContext, build_tools

# Pinned per iteration and recorded per run.
DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 8192
DEFAULT_MAX_ITERATIONS = 30


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    def add(self, u: Any) -> None:
        self.input_tokens += getattr(u, "input_tokens", 0) or 0
        self.output_tokens += getattr(u, "output_tokens", 0) or 0
        self.cache_creation_input_tokens += getattr(u, "cache_creation_input_tokens", 0) or 0
        self.cache_read_input_tokens += getattr(u, "cache_read_input_tokens", 0) or 0


@dataclass
class RunResult:
    model: str
    findings: List[Finding]
    usage: Usage
    turns: int
    wall_clock_s: float
    stop_reason: Optional[str]
    thinking: Optional[str]

    def to_record(self) -> Dict[str, Any]:
        """A flat, JSONL-friendly record of one run."""
        return {
            "model": self.model,
            "thinking": self.thinking,
            "turns": self.turns,
            "wall_clock_s": round(self.wall_clock_s, 3),
            "stop_reason": self.stop_reason,
            "usage": asdict(self.usage),
            "findings": [asdict(f) for f in self.findings],
        }


def _first_user_message(diff_text: str, task_spec: Optional[str],
                        trace: Optional[str] = None) -> str:
    """Iteration-specific content that lands AFTER the cached prefix.

    For the I0 baseline this is the diff alone. Later iterations add the task
    spec (I2a) or a trace (I2b) here without touching the stable prefix.
    """
    parts: List[str] = []
    if task_spec:
        parts.append(f"Task this change was meant to accomplish:\n{task_spec}\n")
    if trace:
        parts.append(
            "The coding agent that wrote this change left the following reasoning "
            f"trace:\n<coder_trace>\n{trace}\n</coder_trace>\n"
        )
    parts.append(
        "Review the diff below. Start by calling get_diff, then read whatever "
        "surrounding code you need before reporting findings.\n\n"
        f"```diff\n{diff_text}\n```"
    )
    return "\n".join(parts)


def review_diff(
    client: Anthropic,
    ctx: ReviewContext,
    *,
    model: str = DEFAULT_MODEL,
    task_spec: Optional[str] = None,
    trace: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    thinking: Optional[str] = "adaptive",
    effort: Optional[str] = None,
    cache_prefix: bool = True,
) -> RunResult:
    """Run one review over ctx.diff_text and return a fully-accounted RunResult.

    Findings accumulate in ctx.findings as the model calls report_finding.
    """
    tools = build_tools(ctx)

    # Stable prefix: system prompt as a single cached text block. The API lays
    # out tools then system before the messages, so a cache_control breakpoint on
    # the system block caches the tool definitions plus the prompt together.
    system_block: Dict[str, Any] = {"type": "text", "text": SYSTEM_PROMPT}
    if cache_prefix:
        system_block["cache_control"] = {"type": "ephemeral"}

    messages = [
        {"role": "user", "content": _first_user_message(ctx.diff_text, task_spec, trace)}
    ]

    kwargs: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": [system_block],
        "messages": messages,
        "tools": tools,
        "max_iterations": max_iterations,
    }
    if thinking:
        kwargs["thinking"] = thinking if isinstance(thinking, dict) else {"type": thinking}
    # Opus 4.8 controls reasoning depth via output_config.effort (with adaptive
    # thinking), not a thinking budget -- this is the I1 sweep knob.
    if effort:
        kwargs["output_config"] = {"effort": effort}

    usage = Usage()
    turns = 0
    stop_reason: Optional[str] = None

    start = time.monotonic()
    runner = client.beta.messages.tool_runner(**kwargs)
    for message in runner:
        turns += 1
        usage.add(message.usage)
        stop_reason = message.stop_reason
    wall = time.monotonic() - start

    return RunResult(
        model=model,
        findings=list(ctx.findings),
        usage=usage,
        turns=turns,
        wall_clock_s=wall,
        stop_reason=stop_reason,
        thinking=thinking,
    )

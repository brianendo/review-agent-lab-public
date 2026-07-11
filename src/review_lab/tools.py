"""The fixed reviewer tool set.

Five tools, documented like an API, arguments designed so mistakes are
structurally hard (the agent-computer interface discipline):

    read_file, list_files, grep_repo   -- read the repo
    get_diff                           -- re-anchor on what changed
    report_finding                     -- the only write

No bash, no writes to disk, no network. The reviewer reads and reports.

Tools close over a per-run ReviewContext (repo root, the diff text, and a
findings collector), built fresh for each run by build_tools().
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal

from anthropic import beta_tool

# Bounds that keep any single tool result small and predictable.
MAX_LIST_RESULTS = 200
MAX_GREP_MATCHES = 100
MAX_FILE_BYTES = 200_000


@dataclass
class Finding:
    file: str
    line: int
    severity: Literal["low", "medium", "high"]
    confidence: Literal["low", "medium", "high"]
    summary: str
    failure_scenario: str


@dataclass
class ReviewContext:
    """Per-run state the tools operate over."""

    repo_root: Path
    diff_text: str
    findings: List[Finding] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.repo_root = self.repo_root.resolve()


def _resolve_in_repo(repo_root: Path, rel_path: str) -> Path:
    """Resolve a repo-relative path, rejecting any escape from the repo root."""
    candidate = (repo_root / rel_path).resolve()
    if candidate != repo_root and repo_root not in candidate.parents:
        raise ValueError(
            f"path {rel_path!r} escapes the repository root; use repo-relative paths only"
        )
    return candidate


def build_tools(ctx: ReviewContext) -> list:
    """Build the five tools bound to a ReviewContext.

    Returns a list of anthropic beta_tool objects ready to hand to tool_runner.
    """

    @beta_tool
    def read_file(path: str, start_line: int = 1, end_line: int = 0) -> str:
        """Read a text file from the repository, with line numbers.

        Paths are repo-relative (e.g. "backtest/engine.py"); absolute paths and
        paths that escape the repo are rejected. Omit end_line (or pass 0) to
        read to the end of the file. Reads at most a bounded number of bytes.

        Args:
            path: Repo-relative path to the file.
            start_line: 1-indexed first line to return (default 1).
            end_line: 1-indexed last line to return; 0 means end of file.
        """
        target = _resolve_in_repo(ctx.repo_root, path)
        if not target.is_file():
            raise ValueError(f"no such file: {path!r}")
        data = target.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            data = data[:MAX_FILE_BYTES]
        lines = data.decode("utf-8", errors="replace").splitlines()
        start = max(start_line, 1)
        stop = len(lines) if end_line <= 0 else min(end_line, len(lines))
        if start > len(lines):
            return f"(file has {len(lines)} lines; start_line {start_line} is past the end)"
        width = len(str(stop))
        numbered = [f"{i:>{width}}\t{lines[i - 1]}" for i in range(start, stop + 1)]
        return "\n".join(numbered)

    @beta_tool
    def list_files(glob_pattern: str = "**/*") -> str:
        """List repository files matching a glob pattern, one per line.

        Patterns are evaluated from the repo root (e.g. "backtest/*.py",
        "**/*.py"). Directories and dotfiles are skipped. Result count is capped;
        if truncated, the last line says so.

        Args:
            glob_pattern: A glob relative to the repo root (default "**/*").
        """
        matches: List[str] = []
        for p in sorted(ctx.repo_root.glob(glob_pattern)):
            if not p.is_file():
                continue
            rel = p.relative_to(ctx.repo_root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            matches.append(str(rel))
            if len(matches) >= MAX_LIST_RESULTS:
                matches.append(f"... (truncated at {MAX_LIST_RESULTS} results)")
                break
        return "\n".join(matches) if matches else "(no files match)"

    @beta_tool
    def grep_repo(regex: str, glob: str = "**/*.py") -> str:
        """Search repository files for a regex, returning file:line: match lines.

        Searches files matching `glob` (default Python files). Case-sensitive.
        Match count is capped; if truncated, the last line says so.

        Args:
            regex: A Python regular expression to search for.
            glob: Glob of files to search, relative to the repo root.
        """
        try:
            pattern = re.compile(regex)
        except re.error as exc:
            raise ValueError(f"invalid regex: {exc}") from exc
        hits: List[str] = []
        for p in sorted(ctx.repo_root.glob(glob)):
            if not p.is_file() or any(part.startswith(".") for part in p.relative_to(ctx.repo_root).parts):
                continue
            rel = p.relative_to(ctx.repo_root)
            try:
                text = p.read_text("utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    hits.append(f"{rel}:{lineno}: {line.strip()}")
                    if len(hits) >= MAX_GREP_MATCHES:
                        hits.append(f"... (truncated at {MAX_GREP_MATCHES} matches)")
                        return "\n".join(hits)
        return "\n".join(hits) if hits else "(no matches)"

    @beta_tool
    def get_diff() -> str:
        """Return the unified diff currently under review.

        Always available for re-anchoring on exactly what changed.
        """
        return ctx.diff_text

    @beta_tool(strict=True)
    def report_finding(
        file: str,
        line: int,
        severity: Literal["low", "medium", "high"],
        confidence: Literal["low", "medium", "high"],
        summary: str,
        failure_scenario: str,
    ) -> str:
        """Record one bug you found. This is the only way to record a result.

        Call once per distinct issue. Anchor to a real file and line in the
        current repository.

        Args:
            file: Repo-relative path where the bug lives.
            line: 1-indexed line the finding anchors to.
            severity: Impact if the bug triggers: low, medium, or high.
            confidence: How sure you are this is a real bug: low, medium, or high.
            summary: One sentence stating the defect.
            failure_scenario: Concrete input/state that triggers it and the wrong
                result it produces.
        """
        ctx.findings.append(
            Finding(
                file=file,
                line=line,
                severity=severity,
                confidence=confidence,
                summary=summary,
                failure_scenario=failure_scenario,
            )
        )
        return f"recorded finding #{len(ctx.findings)} at {file}:{line}"

    return [read_file, list_files, grep_repo, get_diff, report_finding]

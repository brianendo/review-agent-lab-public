"""Generate an I2b case: run a coder agent on a task, capture (code, trace).

    python tools/make_coder_case.py <case_id> <filename> <coder_model> "<task>"

Runs the coder (default: a weaker model, which is likelier to make AND rationalize
a subtle mistake -- the blind-spot the I2b arm tests). Captures the coder's
extended-thinking trace and the code it produced, and writes an evalset case with
`coder_trace` in the manifest. You then inspect the code, seed/confirm ground
truth, write `coder_trace_summary`, and run the 3-arm review comparison:

    runner --cases <case_id> --strict                 # diff only  (baseline)
    runner --cases <case_id> --strict --trace full     # diff + full coder trace
    runner --cases <case_id> --strict --trace summary  # diff + 1-2k trace summary

Trace inclusion is capped in the runner so trace length is not a confound.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from anthropic import Anthropic

from review_lab.run_once import REPO_ROOT, load_dotenv

CODER_PROMPT = (
    "You are a coding agent. Implement the following in Python.\n"
    "First, in a <reasoning>...</reasoning> block, think out loud about your "
    "approach and the edge cases, and justify your key decisions. Then output the "
    "final module in a single ```python fenced block.\n\nTask: {task}"
)


def main() -> None:
    case_id, filename, coder_model, task = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    load_dotenv(REPO_ROOT / ".env")
    client = Anthropic()
    resp = client.messages.create(
        model=coder_model,
        max_tokens=4000,
        messages=[{"role": "user", "content": CODER_PROMPT.format(task=task)}],
    )
    text = "".join(getattr(b, "text", "") for b in resp.content if b.type == "text")
    rm = re.search(r"<reasoning>(.*?)</reasoning>", text, re.S)
    thinking = (rm.group(1).strip() if rm else "")
    m = re.search(r"```python\n(.*?)```", text, re.S)
    code = (m.group(1) if m else text).strip() + "\n"

    d = REPO_ROOT / "evalset" / case_id
    (d / "repo").mkdir(parents=True, exist_ok=True)
    (d / "base").mkdir(parents=True, exist_ok=True)
    (d / "repo" / filename).write_text(code, "utf-8")
    (d / "base" / filename).write_text(f'"""{task[:70]}"""\n', "utf-8")
    manifest = {
        "diff_id": case_id, "repo": "coder-generated",
        "source_commit": f"coder agent ({coder_model})", "task_spec": task,
        "files": [filename], "bugs": [],
        "coder_model": coder_model,
        "coder_trace": thinking,
        "coder_trace_summary": "",
        "provenance": {"class": "clean", "source": "coder-generated",
                       "model_cutoff_status": "na",
                       "note": "code + reasoning trace from a coder agent; I2b process-context arm"},
    }
    (d / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    print(f"wrote {case_id}: {len(code)} chars code, {len(thinking)} chars trace")
    print("=== CODE ===\n" + code)
    print("=== TRACE (first 1200 chars) ===\n" + thinking[:1200])


if __name__ == "__main__":
    main()

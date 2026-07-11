"""Extract a real commit from one of the user's repos into an evalset case.

    python tools/extract_case.py <repo_path> <commit> <case_id> [--include GLOB ...]

Produces evalset/<case_id>/ with:
    repo/        the FULL source tree at the COMMIT (filtered: no data/binaries),
                 so the reviewer's read/grep/list tools see a self-consistent
                 codebase and imports resolve -- like a real clone. This is what
                 CodeRabbit/Greptile/Devin give their reviewer.
    base/        only the CHANGED files at the PARENT commit (enough to build the
                 diff; empty file means the change added it).
    diff.patch   base -> repo over the CHANGED files only, unified, a/ b/ headers.
                 The full tree in repo/ is context, NOT part of the reviewed diff.
    manifest.json  diff_id, repo, source_commit, task_spec (commit message),
                   files (the changed set), bugs (preserved across re-extraction).

Seeding workflow:
    1. Edit a changed file under repo/ to inject a bug.
    2. python tools/extract_case.py --regen <case_id>   (rebuilds diff.patch)
    3. Add the bug to manifest.json["bugs"].

Re-running extract on an existing case PRESERVES manifest["bugs"], so refreshing
the snapshot never destroys ground truth (re-apply the seed edits + --regen after).
"""

from __future__ import annotations

import difflib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVALSET = REPO_ROOT / "evalset"

# Reviewable source we snapshot into repo/. Everything else (data, binaries) is
# excluded so snapshots stay lean and grep stays signal-rich.
SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb",
               ".sql", ".sh", ".toml", ".cfg", ".ini", ".yaml", ".yml", ".json",
               ".md", ".txt", ".env.example"}
# Path components that mark a directory we never want in a snapshot.
EXCLUDE_DIRS = {".git", "node_modules", "data", "datasets", "dist", "build",
                "__pycache__", ".venv", "venv", "vendor", ".next", "coverage",
                ".pytest_cache", ".mypy_cache", "target", "out", ".turbo",
                "artifacts", "checkpoints", "cache", "logs"}
MAX_FILE_BYTES = 300_000       # skip individual files larger than this
MAX_SNAPSHOT_BYTES = 8_000_000  # warn if a whole snapshot exceeds this

# Reviewer model knowledge cutoff. Public commits merged before this may be
# memorized (training contamination), so recall on them is not trustworthy.
MODEL_CUTOFF = "2026-01-31"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=True).stdout


def git_show_file(repo: Path, ref: str, path: str) -> str | None:
    """Contents of `path` at `ref`, or None if it did not exist there."""
    r = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _excluded(path: str) -> bool:
    parts = Path(path).parts
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    return Path(path).suffix not in SOURCE_EXTS


def write_tree(dest: Path, path: str, content: str) -> None:
    p = dest / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, "utf-8")


def unified(base: str | None, head: str | None, path: str) -> str:
    a = (base or "").splitlines(keepends=True)
    b = (head or "").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(a, b, fromfile=f"a/{path}", tofile=f"b/{path}"))
    return f"diff --git a/{path} b/{path}\n{diff}" if diff else ""


def build_diff(case_dir: Path, files: list[str]) -> str:
    """diff.patch over the CHANGED files only: base/<f> vs repo/<f>."""
    base_dir, repo_dir = case_dir / "base", case_dir / "repo"
    chunks = []
    for rel in sorted(files):
        bp, rp = base_dir / rel, repo_dir / rel
        base = bp.read_text("utf-8") if bp.is_file() else None
        head = rp.read_text("utf-8") if rp.is_file() else None
        if base != head:
            chunks.append(unified(base, head, rel))
    return "\n".join(c for c in chunks if c)


def snapshot_full_tree(repo: Path, commit: str, dest_repo: Path) -> tuple[int, int, list[str]]:
    """Write the full filtered source tree at `commit` into dest_repo/.

    Returns (n_files, total_bytes, skipped_large).
    """
    tracked = [f for f in git(repo, "ls-tree", "-r", "--name-only", commit).splitlines() if f]
    n, total, skipped = 0, 0, []
    for f in tracked:
        if _excluded(f):
            continue
        content = git_show_file(repo, commit, f)
        if content is None:
            continue
        if len(content.encode("utf-8", "replace")) > MAX_FILE_BYTES:
            skipped.append(f)
            continue
        write_tree(dest_repo, f, content)
        n += 1
        total += len(content)
    return n, total, skipped


def _load_existing_bugs(case_dir: Path) -> list:
    mpath = case_dir / "manifest.json"
    if mpath.is_file():
        try:
            return json.loads(mpath.read_text("utf-8")).get("bugs", [])
        except json.JSONDecodeError:
            return []
    return []


def extract(repo: Path, commit: str, case_id: str, includes: list[str]) -> None:
    parent = git(repo, "rev-parse", f"{commit}^").strip()
    subject = git(repo, "log", "-1", "--format=%s", commit).strip()
    body = git(repo, "log", "-1", "--format=%b", commit).strip()
    changed = [f for f in git(repo, "diff-tree", "--no-commit-id", "--name-only",
                              "-r", commit).splitlines() if f]
    if includes:
        changed = [f for f in changed if any(Path(f).match(g) for g in includes)]
    changed = [f for f in changed if Path(f).suffix in SOURCE_EXTS]
    if not changed:
        sys.exit(f"no reviewable changed files in {commit} (after filters)")

    case_dir = EVALSET / case_id
    preserved_bugs = _load_existing_bugs(case_dir)

    # Clear old snapshot so removed files don't linger.
    for sub in ("repo", "base"):
        d = case_dir / sub
        if d.exists():
            subprocess.run(["rm", "-rf", str(d)], check=True)

    # repo/ = full tree at commit; base/ = changed files at parent.
    n, total, skipped = snapshot_full_tree(repo, commit, case_dir / "repo")
    for f in changed:
        base = git_show_file(repo, parent, f)
        if base is not None:
            write_tree(case_dir / "base", f, base)

    (case_dir / "diff.patch").write_text(build_diff(case_dir, changed) + "\n", "utf-8")
    task_spec = subject + (f"\n\n{body}" if body else "")
    manifest = {
        "diff_id": case_id,
        "repo": repo.name,
        "source_commit": commit,
        "task_spec": task_spec,
        "files": changed,
        "bugs": preserved_bugs,
    }
    (case_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")

    mb = total / 1_000_000
    print(f"extracted {case_id}: {repo.name}@{commit[:8]}")
    print(f"  changed files (in diff): {len(changed)} -> {', '.join(changed)}")
    print(f"  snapshot: {n} source files, {mb:.1f} MB" +
          (f", {len(skipped)} large file(s) skipped" if skipped else ""))
    if total > MAX_SNAPSHOT_BYTES:
        print(f"  WARNING: snapshot exceeds {MAX_SNAPSHOT_BYTES/1e6:.0f} MB; consider tighter --include")
    if preserved_bugs:
        print(f"  preserved {len(preserved_bugs)} seeded bug(s); re-apply seed edits to repo/ then --regen")


def reverse_fix(repo: Path, fix_commit: str, case_id: str, task_spec: str,
                includes: list[str]) -> None:
    """Build a REGRESSION case from a real bug-fix commit.

    The diff under review is the inverse of the fix (correct -> buggy), so the
    reviewer is reviewing the change that introduced the bug the fix later
    corrected. repo/ is the full tree at the fix's PARENT (the buggy world);
    base/ is the fixed version of the changed files; diff.patch = base -> repo.
    task_spec carries the linked issue / PR intent (the external spec).
    """
    parent = git(repo, "rev-parse", f"{fix_commit}^").strip()
    # `git diff <parent>..<fix>` works for both regular and merge commits,
    # unlike diff-tree which is empty on merges.
    changed = [f for f in git(repo, "diff", "--name-only", parent, fix_commit).splitlines() if f]
    if includes:
        changed = [f for f in changed if any(Path(f).match(g) for g in includes)]
    changed = [f for f in changed if Path(f).suffix in SOURCE_EXTS]
    if not changed:
        sys.exit(f"no reviewable changed files in {fix_commit} (after filters)")

    case_dir = EVALSET / case_id
    preserved_bugs = _load_existing_bugs(case_dir)
    for sub in ("repo", "base"):
        d = case_dir / sub
        if d.exists():
            subprocess.run(["rm", "-rf", str(d)], check=True)

    # repo/ = buggy parent tree; base/ = FIXED version of the changed files.
    n, total, skipped = snapshot_full_tree(repo, parent, case_dir / "repo")
    for f in changed:
        fixed = git_show_file(repo, fix_commit, f)
        if fixed is not None:
            write_tree(case_dir / "base", f, fixed)

    (case_dir / "diff.patch").write_text(build_diff(case_dir, changed) + "\n", "utf-8")

    commit_date = git(repo, "show", "-s", "--format=%cI", fix_commit).strip()[:10]
    pre_cutoff = commit_date < MODEL_CUTOFF
    provenance = {
        "class": "contaminated" if pre_cutoff else "clean",
        "source": "public-oss",
        "model_cutoff_status": "pre" if pre_cutoff else "post",
        "note": (f"public repo, fix merged {commit_date} "
                 + ("BEFORE" if pre_cutoff else "after")
                 + f" the {MODEL_CUTOFF} model cutoff"
                 + ("; likely memorized -- contamination control, exclude from headline recall."
                    if pre_cutoff else "; post-cutoff, contamination-clean.")),
    }
    manifest = {
        "diff_id": case_id,
        "repo": repo.name,
        "source_commit": f"{fix_commit} (reversed fix)",
        "commit_date": commit_date,
        "task_spec": task_spec,
        "files": changed,
        "bugs": preserved_bugs,
        "provenance": provenance,
    }
    (case_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    print(f"reverse-fix {case_id}: {repo.name}@{fix_commit[:8]} ({commit_date}) -> regression diff")
    print(f"  changed files: {', '.join(changed)}")
    print(f"  snapshot(parent): {n} files, {total/1e6:.1f} MB; preserved {len(preserved_bugs)} bug(s)")
    if pre_cutoff:
        print(f"  ⚠️  CONTAMINATION: merged {commit_date} < cutoff {MODEL_CUTOFF} -- likely memorized. "
              f"Prefer post-cutoff PRs for trustworthy recall.")


def regen(case_id: str) -> None:
    case_dir = EVALSET / case_id
    files = json.loads((case_dir / "manifest.json").read_text("utf-8"))["files"]
    (case_dir / "diff.patch").write_text(build_diff(case_dir, files) + "\n", "utf-8")
    print(f"regenerated {case_id}/diff.patch over {len(files)} changed file(s)")


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] == "--regen":
        regen(argv[1])
        return
    if argv and argv[0] == "--reverse-fix":
        # --reverse-fix <repo> <fix_commit> <case_id> --spec "..." [--include GLOB ...]
        repo, commit, case_id = Path(argv[1]).expanduser(), argv[2], argv[3]
        spec = argv[argv.index("--spec") + 1] if "--spec" in argv else ""
        inc = argv[argv.index("--include") + 1:] if "--include" in argv else []
        reverse_fix(repo.resolve(), commit, case_id, spec, inc)
        return
    if len(argv) < 3:
        sys.exit(__doc__)
    repo, commit, case_id = Path(argv[0]).expanduser(), argv[1], argv[2]
    includes = argv[argv.index("--include") + 1:] if "--include" in argv else []
    extract(repo.resolve(), commit, case_id, includes)


if __name__ == "__main__":
    main()

# Blind review: xfile-lock-order — opus (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

Both files are already read via the diff. The bug is clear: this is a classic ABBA lock-ordering deadlock.

## Review Report

### Deadlock: inconsistent lock acquisition order between `transfer` and `reconcile`

- **`sync/transfer.py:35-36`** — `transfer()` acquires `accounts_lock` first, then `audit_lock` (order: accounts → audit).
- **`sync/audit.py:11-12`** — `reconcile()` acquires `audit_lock` first, then `accounts_lock` (order: audit → accounts).

**Summary:** The two code paths acquire the same pair of global locks in opposite orders, creating a classic ABBA deadlock.

**Failure scenario:** `reconcile()` runs on the background thread (per the module docstring "runs on a background thread") while `transfer()` runs on a request/worker thread. Thread T calls `transfer()` and acquires `accounts_lock`, then is preempted before acquiring `audit_lock`. Thread A (background) calls `reconcile()` and acquires `audit_lock`, then blocks trying to acquire `accounts_lock` (held by T). Thread T resumes and blocks trying to acquire `audit_lock` (held by A). Neither thread can proceed — both are permanently blocked, hanging money transfers and the audit sweep. Since these locks are plain non-reentrant `threading.Lock()` objects guarding the same two shared account maps, and the whole point of the change is for both paths to run concurrently, this deadlock is reachable under normal operation whenever a transfer and a reconciliation interleave.

**Fix direction (not applied):** both functions must acquire the two locks in the same global order (e.g., always `accounts_lock` then `audit_lock`, or vice versa).

No other issues found in the change.

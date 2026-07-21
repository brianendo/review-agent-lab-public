# Blind review: xfile-lock-order — sonnet (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

## Code Review: xfile-lock-order

**Bug: Lock-order inversion between `transfer()` and `reconcile()` causes a deadlock**

- `sync/transfer.py:6-7` — `transfer()` acquires `accounts_lock` first, then `audit_lock` (nested: `with accounts_lock: with audit_lock:`).
- `sync/audit.py:7-8` — `reconcile()` acquires `audit_lock` first, then `accounts_lock` (nested: `with audit_lock: with accounts_lock:`).

Both locks are plain `threading.Lock()` instances (non-reentrant) defined in `sync/locks.py:4-5` and shared globally across the two modules.

**Failure scenario:**
1. A request-handling thread calls `transfer(src, dst, amount)`. It acquires `accounts_lock` (transfer.py:6) and then blocks trying to acquire `audit_lock` (transfer.py:7).
2. Concurrently, the background audit thread (per the module docstring in audit.py:1, "runs on a background thread") calls `reconcile(accounts)`. It acquires `audit_lock` (audit.py:7) and then blocks trying to acquire `accounts_lock` (audit.py:8).
3. Neither thread can proceed: the transfer thread holds `accounts_lock` and waits on `audit_lock`; the audit thread holds `audit_lock` and waits on `accounts_lock`. This is a classic circular-wait deadlock — both threads hang forever.

Impact: since `reconcile` is explicitly described as running periodically on a background thread while `transfer` presumably runs on request/worker threads, this isn't a rare race — any transfer that overlaps with an audit sweep has a chance to deadlock, and once it does, all subsequent transfers and audit sweeps stall permanently (the locks are never released), effectively hanging the money-transfer path until the process is restarted.

Fix direction (not applied, per instructions): both functions must acquire the two locks in the same global order (e.g., always `accounts_lock` before `audit_lock`, or vice versa).

No other issues found in the diff (the new `sync/locks.py` module itself is correct as a plain lock-definition file).

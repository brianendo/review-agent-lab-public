# Blind review: ext-webhook-idem — sonnet (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

## Code Review: billing/webhook.py (ext-webhook-idem)

**Scope note:** The repo snapshot contains only `billing/webhook.py`; the modules it imports (`billing/ledger.py`, `billing/store.py`) are not present, so claims about their internal behavior are inferred from usage, not verified.

### Bug 1 — No idempotency check against duplicate webhook delivery
**File:** `billing/webhook.py:12-15`
```python
data = event["data"]
order = get_order(data["order_id"])
order.status = "paid"
record_payment(order.id, data["amount"])
```
**Summary:** The handler unconditionally marks the order paid and records a payment on every invocation, with no check against `event["id"]` or the order's current status, even though Stripe (and the docstring itself, which documents `event["id"]`) guarantees at-least-once delivery and explicit redelivery on ambiguous outcomes (e.g., timeouts, 5xx responses, connection resets).

**Failure scenario:** Stripe delivers `payment_intent.succeeded` for order `O123`, amount `5000`. The handler runs successfully — `order.status = "paid"`, `record_payment("O123", 5000)` — but the outbound HTTP response to Stripe is lost (proxy timeout, connection drop before ack). Stripe treats this as a failed delivery per its retry policy and resends the *same* event minutes later. The handler runs again: `get_order("O123")` returns the same order (already `"paid"`, but that's never checked), and `record_payment("O123", 5000)` fires a second time. The ledger now shows two payments for one real charge — double-counted revenue, and any downstream fulfillment/reconciliation process keyed off ledger entries will double-fulfill or flag a phantom discrepancy. `event["id"]` is documented in the docstring as available specifically for this purpose but is never read.

### Bug 2 — Unhandled crash when order lookup fails
**File:** `billing/webhook.py:13-14`
```python
order = get_order(data["order_id"])
order.status = "paid"
```
**Summary:** The return value of `get_order` is used without a None/not-found check, so a lookup miss crashes the handler with an `AttributeError` instead of being handled gracefully.

**Failure scenario:** A race between order creation and webhook delivery — e.g., the PaymentIntent is confirmed and Stripe fires the webhook before the local order-creation transaction commits, or the webhook arrives for an order that was later deleted/refunded and purged — causes `get_order(data["order_id"])` to return `None` (the typical contract for a "not found" lookup). Line 14, `order.status = "paid"`, then raises `AttributeError: 'NoneType' object has no attribute 'status'`, propagating as an unhandled exception. This turns into a 500 to Stripe, triggering automatic retries of the same unresolvable event, compounding with Bug 1 once the order does eventually exist (the retried event now succeeds, but any other now-processed retries create further duplicate-processing risk).

### Bug 3 — Non-atomic status update and payment recording
**File:** `billing/webhook.py:14-15`
```python
order.status = "paid"
record_payment(order.id, data["amount"])
```
**Summary:** The order is marked paid before the payment is durably recorded, with no transaction or rollback wrapping the two operations, so a failure in `record_payment` leaves the order marked paid with no corresponding ledger entry.

**Failure scenario:** `order.status = "paid"` persists immediately (e.g., an ORM object with autocommit, or a store that writes on attribute assignment). `record_payment` then throws (ledger DB connection blip, constraint violation, timeout). The exception propagates out of `handle_payment_succeeded`, Stripe sees a failure and will retry — but the order is *already* `"paid"` in the store. If any other code path (this handler on retry, an admin view, a fulfillment job) treats `order.status == "paid"` as proof a ledger entry exists, the order silently ships/fulfills with no matching payment record, and reconciliation between orders and the ledger will show an order paid with zero corresponding revenue.

### Observation (not counted as a confirmed bug)
`data["amount"]` from the webhook payload is recorded to the ledger with no cross-check against the order's own expected/authorized amount. If signature verification and amount validation happen entirely upstream of this function, this is fine; if not, a malformed or mismatched event body would let an incorrect amount be written to the ledger. Cannot confirm either way since the caller/dispatcher and `billing/store.py` are not in the reviewed snapshot — flagging for the author to verify amount trust boundaries are enforced somewhere in the pipeline.

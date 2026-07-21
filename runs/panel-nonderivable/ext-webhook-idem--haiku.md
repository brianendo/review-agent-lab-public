# Blind review: ext-webhook-idem — haiku (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

## Code Review Report

### Bug 1: No Idempotency Protection for Webhook Duplicates
**Location:** billing/webhook.py, lines 6-16

**Summary:** Function lacks idempotency checks, allowing duplicate webhook deliveries to process multiple times.

**Failure Scenario:** Stripe webhook service retransmits the same `payment_intent.succeeded` event (normal behavior when webhook handler doesn't immediately acknowledge). The function processes the event twice: `record_payment(order.id, data["amount"])` is called twice with identical inputs. If the ledger doesn't implement idempotency by event ID, duplicate payment entries are recorded, inflating order revenue metrics.

---

### Bug 2: Missing Database Persistence After Order Status Update
**Location:** billing/webhook.py, line 14

**Summary:** Order status is mutated in memory but never explicitly saved to the database.

**Failure Scenario:** Function executes successfully, returns `{"received": True}`, and the order object's `status` attribute is set to "paid" in the Python process. However, since there is no call to `order.save()`, `db.commit()`, or equivalent, the change is never flushed to the database. When querying the database moments later, `order.status` remains "pending", causing downstream systems to treat the order as unpaid.

---

### Bug 3: Unvalidated Dictionary Access on Webhook Payload
**Location:** billing/webhook.py, lines 12-15

**Summary:** Code accesses nested dictionary keys without checking for their presence, will crash on malformed payloads.

**Failure Scenario:** Stripe sends a webhook with missing or malformed `data` structure (e.g., `{"type": "payment_intent.succeeded"}` without `"data"` key). Line 12 (`data = event["data"]`) raises `KeyError`, handler crashes without returning an HTTP response. Stripe interprets the 5xx error as delivery failure and retries the webhook repeatedly, adding load to the system.

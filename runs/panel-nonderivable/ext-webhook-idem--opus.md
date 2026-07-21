# Blind review: ext-webhook-idem — opus (2026-07-20 re-run)

Rig: blind Claude Code subagent (fresh context, no manifest, no seed knowledge),
neutral prompt: read `diff.patch` + `repo/`, report file:line, summary, and a
concrete failure scenario per bug. Verbatim report below.

---

I've reviewed the change. The repo snapshot contains only `billing/webhook.py`; the imported modules `billing.ledger` and `billing.store` are not included, so I reviewed the handler's logic and reasoned about its collaborators from the docstring contract.

## Review Report

**1. Missing idempotency — duplicate webhook delivery double-records the payment (billing/webhook.py:15, primary bug)**
Stripe delivers webhooks with at-least-once semantics: the same event (same `event["id"]`) is retried on any network timeout, non-2xx response, or Stripe-side retry. This handler unconditionally calls `record_payment(order.id, data["amount"])` on every invocation with no dedup against `event["id"]` (or against the order's already-paid state). The branch is literally named `...webhook-idem`, but no idempotency is actually implemented.
Failure scenario: Stripe sends `evt_123` for `order_id=ord_1, amount=5000`. Handler records a 5000 payment and returns. Stripe's connection to your endpoint times out (or a later delivery is retried), so it re-delivers `evt_123`. The handler runs again and records a *second* 5000 payment. The ledger now shows 10000 for a 5000 order — revenue is double-counted and any downstream balance/fulfillment keyed off the ledger is wrong.

**2. `order.status = "paid"` may never be persisted (billing/webhook.py:14, needs store.py to confirm)**
The handler mutates the in-memory attribute but never calls a save/commit and doesn't write the change back through `billing.store`. Whether this persists depends entirely on `get_order`'s return type (a live session-tracked ORM row would auto-persist; a detached DTO/dataclass would not). If `get_order` returns a plain object, the "paid" status is silently lost after the request, while the ledger still records the payment — leaving orders permanently stuck in the pre-paid status. I could not verify because `billing/store.py` is absent from the snapshot.

**3. No verification that the event/amount is trustworthy (billing/webhook.py:12-15)**
The docstring states `event` is "the parsed JSON body," and the handler trusts `data["order_id"]` and `data["amount"]` directly. If Stripe signature verification is not performed by the (unseen) route/caller before this function, anyone who can POST to the webhook endpoint can forge a `payment_intent.succeeded` payload for any `order_id` with any `amount`, marking arbitrary orders paid and injecting ledger entries. Additionally, `amount` is taken from the webhook rather than validated against the order's expected total, so a mismatched amount is recorded verbatim. This is only a bug if verification isn't done upstream — flagging because nothing in the reviewed change performs it.

**4. No handling for missing fields or missing order (billing/webhook.py:12-13, minor/robustness)**
`event["data"]`, `data["order_id"]`, and `data["amount"]` will raise `KeyError` on a malformed payload, and if `get_order` returns `None` for an unknown/deleted order, line 14 raises `AttributeError`. Either causes the handler to throw a 500, which Stripe treats as a failure and *retries* — compounding issue #1.

The headline, high-confidence bug is #1: this payment webhook handler is not idempotent despite that being the stated purpose of the branch.

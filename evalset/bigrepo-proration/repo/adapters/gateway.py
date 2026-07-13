"""Payment gateway stub."""


def charge(account, amount):
    return {"ok": True, "amount_cents": amount.cents}

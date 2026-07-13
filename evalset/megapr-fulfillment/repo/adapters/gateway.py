"""Payment gateway stub."""


def charge(customer_id, amount):
    return {"ok": True, "amount": amount.cents}


def refund(customer_id, amount):
    return {"ok": True, "amount": amount.cents}

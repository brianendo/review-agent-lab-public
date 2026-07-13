from calc import refund_amount, restock_fee, loyalty_points


def test_refund_amount():
    # $50.00 item, $4.00 sales tax charged at purchase.
    assert refund_amount(5000, 400) == 5000


def test_restock_fee():
    # 15% restocking fee on a $300.00 item.
    assert restock_fee(30000) == 4500


def test_loyalty_points():
    # $100.00 order with a $30.00 discount applied.
    assert loyalty_points(10000, 3000) == 100

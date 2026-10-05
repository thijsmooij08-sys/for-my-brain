from decimal import Decimal

from polytrader.domain.market import BookLevel, OrderBook


def test_buy_estimate_walks_ask_levels_without_midpoint_fill() -> None:
    book = OrderBook(
        token_id="yes-token",
        bids=(BookLevel(Decimal("0.48"), Decimal("100")),),
        asks=(
            BookLevel(Decimal("0.51"), Decimal("2")),
            BookLevel(Decimal("0.53"), Decimal("3")),
        ),
    )

    estimate = book.estimate_buy(Decimal("4"))

    assert estimate.filled_quantity == Decimal("4")
    assert estimate.notional == Decimal("2.08")
    assert estimate.vwap == Decimal("0.52")
    assert estimate.remaining_quantity == Decimal("0")


def test_buy_estimate_is_partial_when_book_depth_is_insufficient() -> None:
    book = OrderBook(token_id="yes-token", bids=(), asks=(BookLevel(Decimal("0.51"), Decimal("2")),))

    estimate = book.estimate_buy(Decimal("3"))

    assert estimate.filled_quantity == Decimal("2")
    assert estimate.remaining_quantity == Decimal("1")

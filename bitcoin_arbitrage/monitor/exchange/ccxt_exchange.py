from __future__ import annotations

import os
from typing import Any

import ccxt

from bitcoin_arbitrage.monitor.currency import CurrencyPair
from bitcoin_arbitrage.monitor.exchange import Exchange, BTCAmount
from bitcoin_arbitrage.monitor.log import setup_logger
from bitcoin_arbitrage.monitor.order import Order, OrderState

logger = setup_logger("CcxtExchange")


def _currency_pair_to_ccxt_symbol(pair: CurrencyPair) -> str:
    # "BTC/EUR" -> "BTC/EUR"
    return pair.value


class CcxtExchange(Exchange):
    """
    Modern REST adapter using CCXT. Supports ticker updates (ask/bid).
    Trading/order endpoints are intentionally not implemented yet.
    """

    def __init__(self, exchange_id: str, currency_pair: CurrencyPair):
        super().__init__(currency_pair)
        self.exchange_id = exchange_id

        timeout_ms = int(os.environ.get("CCXT_TIMEOUT_MS", "8000"))
        enable_rate_limit = os.environ.get("CCXT_ENABLE_RATE_LIMIT", "1") in ("1", "true", "yes", "on")

        cls = getattr(ccxt, exchange_id, None)
        if cls is None:
            raise ValueError(f"Unknown CCXT exchange id: {exchange_id}")

        self._client = cls(
            {
                "enableRateLimit": enable_rate_limit,
                "timeout": timeout_ms,
            }
        )

    @property
    def name(self) -> str:
        return f"ccxt:{self.exchange_id}"

    @property
    def currency_pair_api_representation(self) -> str:
        return _currency_pair_to_ccxt_symbol(self.currency_pair)

    @property
    def base_url(self) -> str:
        return ""

    @property
    def ticker_url(self) -> str:
        return ""

    def update_prices(self) -> bool:
        symbol = self.currency_pair_api_representation
        try:
            ticker: dict[str, Any] = self._client.fetch_ticker(symbol)
        except Exception as exc:
            logger.warning(f"CCXT ticker fetch failed for {self.exchange_id} {symbol}: {exc}")
            return False

        ask = ticker.get("ask")
        bid = ticker.get("bid")
        if ask is None or bid is None:
            logger.warning(f"CCXT ticker missing ask/bid for {self.exchange_id} {symbol}: {ticker}")
            return False

        try:
            self.last_ask_price = float(ask)
            self.last_bid_price = float(bid)
        except (TypeError, ValueError):
            logger.warning(f"CCXT ticker ask/bid not numeric for {self.exchange_id} {symbol}: {ask=} {bid=}")
            return False

        return True

    def limit_sell_order(self, amount: BTCAmount, limit: float) -> Order:
        raise NotImplementedError

    def limit_buy_order(self, amount: BTCAmount, limit: float) -> Order:
        raise NotImplementedError

    def get_order_state(self, order: Order) -> OrderState:
        raise NotImplementedError


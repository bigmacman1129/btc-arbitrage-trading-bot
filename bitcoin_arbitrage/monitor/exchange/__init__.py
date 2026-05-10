import json
import os
import sys
import requests

from abc import ABC, abstractmethod
from typing import Optional

from bitcoin_arbitrage.monitor.currency import CurrencyPair, BTCAmount
from bitcoin_arbitrage.monitor.order import Order, OrderState

from bitcoin_arbitrage.monitor.log import setup_logger

logger = setup_logger('Exchange')
REQUEST_TIMEOUT_SECONDS = int(os.environ.get('EXCHANGE_REQUEST_TIMEOUT_SECONDS', '8'))
REQUEST_MAX_ATTEMPTS = max(1, int(os.environ.get('EXCHANGE_REQUEST_MAX_ATTEMPTS', '2')))
_SESSION = requests.Session()
_SESSION.headers.update({'User-Agent': 'bitcoin-arbitrage-trading-bot/modernized'})


class Exchange(ABC):
    @property
    def name(self) -> str:
        return str(self.__class__.__name__)

    @property
    @abstractmethod
    def currency_pair_api_representation(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def base_url(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def ticker_url(self) -> str:
        raise NotImplementedError

    def _extract_prices_from_ticker(self, payload: object) -> tuple[float, float]:
        """
        Return (ask, bid) from exchange ticker payload.
        Default implementation expects dict payloads with 'ask' and 'bid' fields.
        """
        if not isinstance(payload, dict):
            raise TypeError('Ticker payload must be a dict for default parser.')
        ask = float(payload.get('ask'))
        bid = float(payload.get('bid'))
        return ask, bid

    def __init__(self, currency_pair: CurrencyPair):
        self.currency_pair = currency_pair
        self.last_ask_price: Optional[float] = None
        self.last_bid_price: Optional[float] = None

    def __str__(self):
        return f"{self.name} ({self.currency_pair.value})"

    @property
    def summary(self):
        return self.__str__() + f"\n - Ask: {self.last_ask_price}" \
                                f"\n - Bid: {self.last_bid_price}"

    # ToDo: Make async
    def update_prices(self) -> bool:
        last_request_error: Optional[Exception] = None
        last_status_code: Optional[int] = None

        for attempt in range(1, REQUEST_MAX_ATTEMPTS + 1):
            try:
                response = _SESSION.get(self.ticker_url, timeout=REQUEST_TIMEOUT_SECONDS)
            except requests.RequestException as exc:
                last_request_error = exc
                if attempt < REQUEST_MAX_ATTEMPTS:
                    continue
                logger.warning(f'Could not update prices for {self}. Request failed: {exc}')
                return False

            last_status_code = response.status_code
            if response.status_code != 200:
                # Retry transient upstream failures (5xx) and rate limiting (429).
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < REQUEST_MAX_ATTEMPTS:
                        continue
                logger.warning(
                    f'Could not update prices for {self}. API returned status {response.status_code}.'
                )
                return False

            try:
                json_response = response.json()
                ask, bid = self._extract_prices_from_ticker(json_response)
                self.last_ask_price = ask
                self.last_bid_price = bid
                return True
            except (json.decoder.JSONDecodeError, TypeError, ValueError):
                logger.error(f'Could not update prices for {self}. Error on json processing:')
                logger.error(sys.exc_info())
                return False

        logger.warning(
            f'Could not update prices for {self}. Last status={last_status_code}, '
            f'last error={last_request_error}.'
        )
        return False

    @abstractmethod
    def limit_buy_order(self, amount: BTCAmount, limit: float) -> Order:
        raise NotImplementedError

    @abstractmethod
    def limit_sell_order(self, amount: BTCAmount, limit: float) -> Order:
        raise NotImplementedError

    def get_order_state(self, order: Order) -> OrderState:
        raise NotImplementedError

    def cancel_order(self, order: Order) -> None:
        raise NotImplementedError

    # @abstractmethod
    # def get_account_balance(self) -> FiatAmount:
    #     raise NotImplementedError('Implement get_account_balance() for your exchange.')
    #

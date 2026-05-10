import base64
import datetime
import hmac

import hashlib
import os
import requests
from requests.auth import AuthBase

from bitcoin_arbitrage.monitor.currency import CurrencyPair
from bitcoin_arbitrage.monitor.exchange import Exchange, BTCAmount
from bitcoin_arbitrage.monitor.log import setup_logger
from bitcoin_arbitrage.monitor.order import Order, OrderState, OrderId

logger = setup_logger('gdax')


# Create custom authentication
class GdaxAuth(AuthBase):
    def __init__(self, key: str, secret: str, passphrase: str):
        self.api_key = key
        self.secret_key = secret
        self.passphrase = passphrase

    def __call__(self, request):
        if not self.api_key or not self.secret_key or not self.passphrase:
            raise ValueError('Missing Coinbase Exchange API credentials (key/secret/passphrase).')
        timestamp = str(int(datetime.datetime.utcnow().timestamp()))
        body = request.body or b''
        if isinstance(body, str):
            body = body.encode('utf-8')
        message = f"{timestamp}{request.method}{request.path_url}".encode('utf-8') + body
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request


class Gdax(Exchange):
    # GDAX was renamed to Coinbase Pro and later folded into Coinbase Exchange.
    base_url = "https://api.exchange.coinbase.com"

    currency_pair_api_representation = {
        CurrencyPair.BTC_USD: "BTC-USD",
        CurrencyPair.BTC_EUR: "BTC-EUR",

        CurrencyPair.ETH_USD: "ETH-USD",
        CurrencyPair.ETH_EUR: "ETH-EUR",
    }

    def __init__(self,
                 currency_pair: CurrencyPair,
                 api_key: str | None = None,
                 secret_key: str | None = None,
                 passphrase: str | None = None):
        super().__init__(currency_pair)
        # Avoid importing `settings` here (it imports Exchange classes and creates circular imports).
        api_key = api_key if api_key is not None else os.environ.get('GDAX_KEY')
        secret_key = secret_key if secret_key is not None else os.environ.get('GDAX_SECRET')
        passphrase = passphrase if passphrase is not None else os.environ.get('GDAX_PASSPHRASE')
        # Optional modern env names (keeps backward compatibility with GDAX_*)
        api_key = api_key or os.environ.get('COINBASE_EXCHANGE_KEY')
        secret_key = secret_key or os.environ.get('COINBASE_EXCHANGE_SECRET')
        passphrase = passphrase or os.environ.get('COINBASE_EXCHANGE_PASSPHRASE')
        self.auth = GdaxAuth(api_key, secret_key, passphrase)

    @property
    def ticker_url(self) -> str:
        return f"{self.base_url}/products/{self.currency_pair_api_representation[self.currency_pair]}/ticker"

    def _place_limit_order(self, side: str, amount: BTCAmount, limit: float) -> OrderId:
        url = f"{self.base_url}/orders/"
        data = {
            'product_id': self.currency_pair_api_representation.get(self.currency_pair),
            'side': side,
            'size': amount,
            'price': limit,
        }
        response = requests.post(url, json=data, auth=self.auth)
        json = response.json()
        order_id = json.get('id')
        return order_id

    def limit_sell_order(self, amount: BTCAmount, limit: float) -> Order:
        order_id = self._place_limit_order('sell', amount, limit)
        return Order(exchange=self, order_id=order_id)

    def limit_buy_order(self, amount: BTCAmount, limit: float) -> Order:
        order_id = self._place_limit_order('buy', amount, limit)
        return Order(exchange=self, order_id=order_id)

    def get_order_state(self, order: Order) -> OrderState:
        url = f'{self.base_url}/orders/{order.order_id}'
        response = requests.get(url, auth=self.auth)

        if response.status_code == 404:
            logger.info(f'Order {order} doesn\'t return a status, it might be cancelled')
            return OrderState.CANCELLED

        state_string = response.json().get('state')

        if state_string in ['done', 'settled']:
            return OrderState.DONE
        elif state_string in ['open', 'pending']:
            return OrderState.PENDING


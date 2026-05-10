import logging

import os

LOG_LEVEL = logging.INFO

from typing import List

from bitcoin_arbitrage.monitor.currency import CurrencyPair

from bitcoin_arbitrage.monitor.exchange import Exchange
from bitcoin_arbitrage.monitor.exchange.bitfinex import Bitfinex
from bitcoin_arbitrage.monitor.exchange.bitstamp import Bitstamp
from bitcoin_arbitrage.monitor.exchange.ccxt_exchange import CcxtExchange
from bitcoin_arbitrage.monitor.exchange.gdax import Gdax

from bitcoin_arbitrage.monitor.update import UpdateAction
from bitcoin_arbitrage.monitor.update.db_commit import SpreadHistoryToDB
from bitcoin_arbitrage.monitor.update.notification.pushbullet import Pushbullet
from bitcoin_arbitrage.monitor.update.notification.stdout import StdoutNotification
from bitcoin_arbitrage.monitor.update.csv_writer import SpreadHistoryToCSV, LastSpreadsToCSV

EXCHANGES: List[Exchange] = [
    Bitfinex(CurrencyPair.BTC_EUR),

    Bitstamp(CurrencyPair.BTC_EUR),
    Bitstamp(CurrencyPair.ETH_EUR),

    Gdax(CurrencyPair.BTC_EUR),
    Gdax(CurrencyPair.ETH_EUR),
    # Modern alternative via CCXT (example; uncomment to use)
    # CcxtExchange("bitfinex", CurrencyPair.BTC_EUR),
]

UPDATE_ACTIONS: List[UpdateAction] = [
    Pushbullet(spread_threshold=500, api_key='DEBUG'),
    StdoutNotification(spread_threshold=100),
    SpreadHistoryToDB(),
]

UPDATE_INTERVAL = 30  # seconds

TIME_BETWEEN_NOTIFICATIONS = 5 * 60  # Only send a notification every 5 minutes

MINIMUM_SPREAD_TRADING = 200
# Minimum net spread after fees/slippage (recommended to use for trading).
MINIMUM_NET_SPREAD_TRADING = int(os.environ.get('MINIMUM_NET_SPREAD_TRADING', str(MINIMUM_SPREAD_TRADING)))
TRADING_BTC_AMOUNT = 0.5
TRADING_LIMIT_PUFFER = 10  # Fiat Amount
TRADING_ORDER_STATE_UPDATE_INTERVAL = 1
TRADING_TIME_UNTIL_ORDER_CANCELLATION = 30

# Fee & slippage model (basis points = 1/100 of a percent).
# This is a simplified model that approximates taker fees + execution slippage.
DEFAULT_TAKER_FEE_BPS = float(os.environ.get('DEFAULT_TAKER_FEE_BPS', '10'))  # 0.10%
DEFAULT_SLIPPAGE_BPS = float(os.environ.get('DEFAULT_SLIPPAGE_BPS', '5'))     # 0.05%

GDAX_KEY = os.environ.get('GDAX_KEY')
GDAX_SECRET = os.environ.get('GDAX_SECRET')
GDAX_PASSPHRASE = os.environ.get('GDAX_PASSPHRASE')

# Modern Coinbase Exchange env names (recommended)
COINBASE_EXCHANGE_KEY = os.environ.get('COINBASE_EXCHANGE_KEY')
COINBASE_EXCHANGE_SECRET = os.environ.get('COINBASE_EXCHANGE_SECRET')
COINBASE_EXCHANGE_PASSPHRASE = os.environ.get('COINBASE_EXCHANGE_PASSPHRASE')

# Exchange request tuning
# Timeout (seconds) for ticker API requests.
EXCHANGE_REQUEST_TIMEOUT_SECONDS = int(os.environ.get('EXCHANGE_REQUEST_TIMEOUT_SECONDS', '8'))
# Retry attempts for transient request failures/statuses (e.g. timeouts, 429, 5xx).
EXCHANGE_REQUEST_MAX_ATTEMPTS = int(os.environ.get('EXCHANGE_REQUEST_MAX_ATTEMPTS', '2'))

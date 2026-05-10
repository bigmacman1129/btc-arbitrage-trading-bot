from bitcoin_arbitrage.monitor.currency import CurrencyPair
from bitcoin_arbitrage.monitor.exchange import Exchange, BTCAmount
from bitcoin_arbitrage.monitor.log import setup_logger
from bitcoin_arbitrage.monitor.order import Order, OrderState

logger = setup_logger('Bitfinex')


class Bitfinex(Exchange):
    base_url = "https://api-pub.bitfinex.com/v2"

    currency_pair_api_representation = {
        CurrencyPair.BTC_USD: "tBTCUSD",
        CurrencyPair.BTC_EUR: "tBTCEUR",

        CurrencyPair.ETH_USD: "tETHUSD",
        # CurrencyPair.ETH_EUR: "ETHEUR",  # Does not exist apparently
    }

    @property
    def ticker_url(self) -> str:
        return f"{self.base_url}/ticker/{self.currency_pair_api_representation[self.currency_pair]}"

    def _extract_prices_from_ticker(self, payload: object) -> tuple[float, float]:
        # Bitfinex v2 ticker payload: [BID, BID_SIZE, ASK, ASK_SIZE, ...]
        if not isinstance(payload, list) or len(payload) < 3:
            raise TypeError('Unexpected Bitfinex ticker payload format.')
        bid = float(payload[0])
        ask = float(payload[2])
        return ask, bid

    def limit_sell_order(self, amount: BTCAmount, limit: float) -> Order:
        raise NotImplementedError

    def limit_buy_order(self, amount: BTCAmount, limit: float) -> Order:
        raise NotImplementedError

    def get_order_state(self, order: Order) -> OrderState:
        raise NotImplementedError

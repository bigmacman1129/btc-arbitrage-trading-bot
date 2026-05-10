import asyncio
import itertools
from datetime import datetime
from typing import List, Tuple
import time

from bitcoin_arbitrage.monitor import settings
from bitcoin_arbitrage.monitor.exchange import Exchange
from bitcoin_arbitrage.monitor.log import setup_logger
from bitcoin_arbitrage.monitor.spread_detection import Spread, SpreadMissingPriceError, SpreadDifferentCurrenciesError

logger = setup_logger('Monitor')


class Monitor:
    def __init__(self) -> None:
        self._last_spreads: List[Spread] = []
        self._consecutive_all_exchange_failures = 0

    async def update(self) -> None:
        while True:
            cycle_started = time.monotonic()
            logger.debug('Update...')

            successful_exchange_updates = 0
            failed_exchange_updates = 0
            for exchange in settings.EXCHANGES:
                try:
                    if exchange.update_prices():
                        successful_exchange_updates += 1
                    else:
                        failed_exchange_updates += 1
                except Exception:
                    # Keep monitor loop alive even if one exchange adapter fails.
                    logger.exception(f'Exchange update failed for {exchange}.')
                    failed_exchange_updates += 1

            if failed_exchange_updates > 0 and successful_exchange_updates == 0:
                self._consecutive_all_exchange_failures += 1
            else:
                self._consecutive_all_exchange_failures = 0

            spreads = self._calculate_spreads()
            timestamp = datetime.now().timestamp()

            skipped_actions = False
            if self._consecutive_all_exchange_failures >= 3:
                skipped_actions = True
                logger.warning(
                    'Skipping update actions because all exchanges failed for %s consecutive cycles.',
                    self._consecutive_all_exchange_failures,
                )
            else:
                for action in settings.UPDATE_ACTIONS:
                    try:
                        action.run(spreads, settings.EXCHANGES, timestamp)  # ToDo: Run every action asynchronously?
                    except Exception:
                        # One failing action (e.g. DB write) should not stop the monitor.
                        logger.exception(f'Update action {action.__class__.__name__} failed.')

            cycle_duration_ms = int((time.monotonic() - cycle_started) * 1000)
            logger.info(
                'cycle_stats exchanges_ok=%s exchanges_failed=%s spreads=%s actions_skipped=%s duration_ms=%s',
                successful_exchange_updates,
                failed_exchange_updates,
                len(spreads),
                skipped_actions,
                cycle_duration_ms,
            )

            await asyncio.sleep(settings.UPDATE_INTERVAL)

    def _calculate_spreads(self) -> List[Spread]:
        combinations: List[Tuple[Exchange, Exchange]] = list(itertools.combinations(settings.EXCHANGES, 2))
        spreads: List[Spread] = []
        for pair in combinations:
            try:
                spread = Spread(exchange_one=pair[0], exchange_two=pair[1])
                if spread.spread > 0:
                    spreads.append(spread)
            except (SpreadMissingPriceError, SpreadDifferentCurrenciesError):
                continue
        return spreads

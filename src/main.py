import signal
import sys
import time
from contextlib import suppress
from threading import active_count
from typing import Dict

from src.config.logger_config import logger
from src.connectors.bybit_connector import BybitConnector
from src.db.migrations.migrate import apply_migrations
from src.db.queries.event_managers import get_all_event_managers
from src.db.queries.portfolios import get_portfolios_by_event_manager_id
from src.db.queries.strategies import get_strategies_by_event_manager_id
from src.db.queries.strategy_subscriptions import get_subscriptions_by_portfolio
from src.event_manager import EventManager
from src.market_data_provider import MarketDataProvider
from src.monitoring import Monitoring
from src.portfolio import Portfolio
from src.strategy.abstract_strategy import AbstractStrategy


def system_kill(*_, **__):
    """Trigger a controlled shutdown when SIGINT/SIGTERM is caught."""
    logger.warning("Shutdown signal received")
    raise KeyboardInterrupt  # handled in main()


class App:
    """Orchestrates the lifetime of trading subsystems."""

    def __init__(self) -> None:
        self._event_managers = []
        self._monitoring = None
        self._live_market = None
        self._backtest_market = None
        self._objects = []

    def _track(self, obj):
        """Remember *obj* so we can stop it later if it exposes .stop()."""
        if hasattr(obj, "stop"):
            self._objects.append(obj)
        return obj

    def _stop_everything(self):
        """Iterate in reverse creation order and call .stop() if defined."""
        logger.info(f"Stopping {len(self._objects)} components...")
        for o in reversed(self._objects):
            with suppress(Exception):
                o.stop()
        while active_count() > 2:
            time.sleep(1)
        logger.info("Shutdown complete!")

    def bootstrap(self) -> None:
        """Run migrations, load managers/strategies/portfolios and wire them."""
        logger.info("Running DB migrations…")
        apply_migrations()

        for em in get_all_event_managers():
            event_manager = EventManager.from_id(em["event_manager_id"])
            self._track(event_manager._order_executor)
            self._track(event_manager)
            self._event_managers.append(event_manager)

        self._live_market = None
        # self._live_market = MarketDataProvider(BybitConnector(testnet=False))
        # self._track(self._live_market)
        self._backtest_market = None
        self._backtest_market = MarketDataProvider(BybitConnector(testnet=False), mode="backtest")
        self._track(self._backtest_market)
        self._wire_existing_objects()
        self._monitoring = self._track(Monitoring())


    def _wire_existing_objects(self) -> None:
        """Fetch strategies/portfolios from DB and subscribe them correctly."""
        for em in self._event_managers:
            market = self._backtest_market if em._mode == "backtest" else self._live_market
            if market is None:
                continue
            strategy_rows = get_strategies_by_event_manager_id(em.event_manager_id)
            portfolio_rows = get_portfolios_by_event_manager_id(em.event_manager_id)

            strategies: Dict[str, AbstractStrategy] = {}
            portfolios: Dict[str, Portfolio] = {}

            for s in strategy_rows:
                strategy = AbstractStrategy.from_id(s["strategy_id"])
                if strategy:
                    strategies[strategy.strategy_id] = strategy
                    timeframe = '1h'
                    if 'timeframe' in strategy.parameters:
                        timeframe = strategy.parameters['timeframe']

                    market.subscribe(strategy, strategy.trading_pair, timeframe)

            all_links = []
            for p in portfolio_rows:
                portfolio = Portfolio.from_id(p["portfolio_id"])
                if portfolio:
                    portfolios[portfolio.portfolio_id] = portfolio
                for link in get_subscriptions_by_portfolio(p["portfolio_id"]):
                    all_links.append(link)
            for link in all_links:
                portfolio = portfolios[str(link["portfolio_id"])]
                strategy = strategies[str(link["strategy_id"])]
                if portfolio and strategy:
                    em.subscribe_portfolio_to_strategy(portfolio, strategy.strategy_id)

            em.start()

    def run_forever(self):
        logger.success("Application started.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.warning("Shutdown initiated …")
            self._stop_everything()


def main() -> None:
    signal.signal(signal.SIGINT, system_kill)
    signal.signal(signal.SIGTERM, system_kill)
    app = App()
    try:
        app.bootstrap()
        app.run_forever()
    except Exception:
        logger.exception("Fatal error – aborting …")
        app._stop_everything()
        sys.exit(1)

if __name__ == "__main__":
    main()

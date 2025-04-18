import time
import uuid
from decimal import Decimal

from src.connectors.bybit_connector import BybitConnector
from src.db.queries.risk_controllers import add_risk_controller
from src.event_manager import EventManager
from src.market_data_provider import MarketDataProvider
from src.monitoring import Monitoring
from src.portfolio import Portfolio
from src.strategy.abstract_strategy import AbstractStrategy
from src.strategy.random_strategy import RandomStrategy
from src.config.logger_config import logger


def create_fake_orders():
    event_manager = EventManager.create_new(mode="live")

    created_ids = event_manager._order_controller.create_order(
        portfolio_id=str(uuid.uuid4()),
        event_manager_id=event_manager.event_manager_id,
        signal_id=str(uuid.uuid4()),
        order_type="market",
        order_category="spot",
        order_side="buy",
        target_price=Decimal("30000"),
        order_status="pending",
        symbol="BTC/USDT",
        base_currency="BTC",
        quote_currency="USDT",
        initial_quantity=Decimal("0.0001")
    )

    event_manager.start()


def create_fake_portfolio():
    event_manager = EventManager.create_new(mode="live")
    event_manager.start()
    strategy = AbstractStrategy.create_strategy(RandomStrategy, event_manager.event_manager_id, "BTC/USDT", "Random", {})
    strategy.start()

    risk_controller_id = add_risk_controller("aggressive", 0.5, 1.5,    {
        'BTC/USDT': 0.5,
        'ETH/USDT': 0.5
    })

    portfolio = Portfolio.create_portfolio(
        event_manager_id=event_manager.event_manager_id,
        risk_controller_id=risk_controller_id,
        portfolio_name="My Test Portfolio",
        managed_assets={"BTC": 0.5, "ETH": 2},
        currency="USDT",
        initial_balance=10000,
        exchange="bybit"
    )

    event_manager.subscribe_portfolio_to_strategy(portfolio, strategy.strategy_id)

    time.sleep(10)
    strategy.stop()
    event_manager.stop()


def create_fake_market_data_provider():
    market = MarketDataProvider(BybitConnector(testnet=True))
    event_manager = EventManager.create_new(mode="live")
    event_manager.start()
    strategy1 = AbstractStrategy.create_strategy(RandomStrategy, event_manager.event_manager_id, "BTC/USDT", "Random",
                                                {})
    strategy2 = AbstractStrategy.create_strategy(RandomStrategy, event_manager.event_manager_id, "BTC/USDT", "Random",
                                                {})
    strategy1.start()
    market.subscribe(strategy1, strategy1.trading_pair, '1m')
    market.subscribe(strategy2, strategy2.trading_pair, '1h')
    time.sleep(30)
    market.stop()
    strategy1.stop()
    strategy2.stop()
    event_manager.stop()


def monitor():
    monitoring = Monitoring()
    monitoring.ohlcv_plot(data='market_data_test/BTC_USDT_1h.csv', volume=True, type='line')


if __name__ == "__main__":
    logger.info("Test in main")
    create_fake_portfolio()

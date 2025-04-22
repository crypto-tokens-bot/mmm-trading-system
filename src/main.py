import time
import uuid
from decimal import Decimal

from src.connectors.bybit_connector import BybitConnector
from src.db.queries.risk_controllers import add_risk_controller
from src.event_manager import EventManager
from src.historical_data_feed import HistoricalDataFeed
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


    market = MarketDataProvider(BybitConnector(testnet=False))
    market.subscribe(strategy, strategy.trading_pair, '1h')

    risk_controller_id = add_risk_controller("aggressive", 0.5, 1.5,    {
        'BTC': 0.8,
        'ETH': 0.5
    })

    portfolio = Portfolio.create_portfolio(
        event_manager_id=event_manager.event_manager_id,
        risk_controller_id=risk_controller_id,
        portfolio_name="My Test Portfolio 4",
        managed_assets={"BTC": Decimal(0.001), "ETH": Decimal(3), "USDT": Decimal(10000)},
        currency="USDT",
        initial_balance=Decimal(10000),
        exchange="bybit"
    )
    monitoring = Monitoring()

    event_manager.subscribe_portfolio_to_strategy(portfolio, strategy.strategy_id)

    time.sleep(43)

    monitoring.stop()
    market.stop()
    event_manager.stop()

def create_backtest():
    event_manager = EventManager.create_new(mode="backtest")
    event_manager.start()

    strategy = AbstractStrategy.create_strategy(RandomStrategy, event_manager.event_manager_id, "BTC/USDT", "Random", {})

    market = MarketDataProvider(BybitConnector(testnet=True), mode='backtest')
    market.subscribe(strategy, strategy.trading_pair, '1h')

    risk_controller_id = add_risk_controller("aggressive", None, None,    {
        'BTC': 0.8,
        'ETH': 0.5
    })

    portfolio = Portfolio.create_portfolio(
        event_manager_id=event_manager.event_manager_id,
        risk_controller_id=risk_controller_id,
        portfolio_name="Backtest 1",
        managed_assets={"BTC": Decimal(0.01), "ETH": Decimal(3), "USDT": Decimal(10000)},
        currency="USDT",
        initial_balance=Decimal(10000),
        exchange="bybit"
    )
    monitoring = Monitoring()

    event_manager.subscribe_portfolio_to_strategy(portfolio, strategy.strategy_id)

    time.sleep(100)

    monitoring.stop()
    market.stop()
    event_manager.stop()

if __name__ == "__main__":
    logger.info("Test in main")
    create_fake_portfolio()

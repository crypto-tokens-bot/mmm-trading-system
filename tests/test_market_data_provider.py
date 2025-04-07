import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd
import asyncio
from pathlib import Path
from loguru import logger

from src.connectors.exchange_connector import ExchangeConnector
from src.market_data_provider import MarketDataProvider


@pytest.fixture
def mock_exchange_connector():
    connector = AsyncMock(spec=ExchangeConnector)
    connector.fetch_ohlcv.return_value = pd.DataFrame({
        'timestamp': [1, 2, 3],
        'open': [100, 101, 102],
        'high': [105, 106, 107],
        'low': [95, 96, 97],
        'close': [102, 103, 104],
        'volume': [1000, 2000, 3000]
    })
    return connector


@pytest.fixture
def data_provider(mock_exchange_connector, tmp_path):
    return MarketDataProvider(mock_exchange_connector, data_directory=str(tmp_path))


@pytest.fixture
def mock_strategy():
    strategy = MagicMock()
    strategy.on_new_data = AsyncMock()
    return strategy


@pytest.mark.asyncio
async def test_subscribe_unsubscribe(data_provider, mock_strategy):
    symbol = "BTC/USDT"
    timeframe = "1h"

    # Test subscribe
    data_provider.subscribe(mock_strategy, symbol, timeframe)
    assert (symbol, timeframe) in data_provider.subscribers
    assert mock_strategy in data_provider.subscribers[(symbol, timeframe)]

    # Test unsubscribe
    data_provider.unsubscribe(mock_strategy, symbol, timeframe)
    assert (symbol, timeframe) not in data_provider.subscribers


@pytest.mark.asyncio
async def test_fetch_and_store_data(data_provider, mock_exchange_connector, tmp_path):
    symbol = "BTC/USDT"
    timeframe = "1h"

    await data_provider.fetch_and_store_data(symbol, timeframe)

    # Check if exchange connector was called
    mock_exchange_connector.fetch_ohlcv.assert_called_once_with(symbol, timeframe, limit=100)

    # Check if file was created
    expected_path = tmp_path / f"{symbol.replace('/', '_')}_{timeframe}.csv"
    assert expected_path.exists()


@pytest.mark.asyncio
async def test_notify_subscribers(data_provider, mock_strategy):
    symbol = "BTC/USDT"
    timeframe = "1h"
    file_path = "test_path.csv"

    data_provider.subscribe(mock_strategy, symbol, timeframe)
    data_provider.notify_subscribers(symbol, timeframe, file_path)

    # Give some time for the async task to start
    await asyncio.sleep(0.1)

    mock_strategy.on_new_data.assert_called_once_with(file_path)


@pytest.mark.asyncio
async def test_run_loop(data_provider, mock_exchange_connector, mock_strategy):
    symbol = "BTC/USDT"
    timeframe = "1h"
    data_provider.subscribe(mock_strategy, symbol, timeframe)

    # Run for a short time and cancel
    task = asyncio.create_task(data_provider.run())
    await asyncio.sleep(0.1)
    task.cancel()

    # Check if fetch was called at least once
    mock_exchange_connector.fetch_ohlcv.assert_called()


@pytest.mark.asyncio
async def test_error_handling(data_provider, mock_exchange_connector, caplog):
    symbol = "BTC/USDT"
    timeframe = "1h"

    # Simulate error in fetch_ohlcv
    mock_exchange_connector.fetch_ohlcv.side_effect = Exception("Test error")

    await data_provider.fetch_and_store_data(symbol, timeframe)

    # Check if error was logged
    assert "Error fetching data for BTC/USDT 1h: Test error" in caplog.text


def test_directory_creation(tmp_path, mock_exchange_connector):
    # Test with non-existent directory
    new_dir = tmp_path / "new_dir"
    provider = MarketDataProvider(mock_exchange_connector, str(new_dir))

    # Just creating the provider shouldn't create the directory
    assert not new_dir.exists()

    # Directory should be created when actually saving data
    asyncio.run(provider.fetch_and_store_data("BTC/USDT", "1h"))
    assert new_dir.exists()


@pytest.mark.asyncio
async def test_multiple_subscribers(data_provider):
    symbol = "BTC/USDT"
    timeframe = "1h"

    strategy1 = MagicMock()
    strategy1.on_new_data = AsyncMock()

    strategy2 = MagicMock()
    strategy2.on_new_data = AsyncMock()

    data_provider.subscribe(strategy1, symbol, timeframe)
    data_provider.subscribe(strategy2, symbol, timeframe)

    file_path = "test_path.csv"
    data_provider.notify_subscribers(symbol, timeframe, file_path)
    await asyncio.sleep(0.1)

    strategy1.on_new_data.assert_called_once_with(file_path)
    strategy2.on_new_data.assert_called_once_with(file_path)
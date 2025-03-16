import asyncio
import os
import db.db_connection as db
from src.connectors.bybit_connector import BybitAsyncConnector

from dotenv import load_dotenv


async def main():
    """
    Entry point for the application.
    Demonstrates how to use the EventManager to add and process events.

    :return: None
    """

    print(db.get_db_client())

    load_dotenv()
    bybit_exchange = BybitAsyncConnector(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'),
                                         testnet=True)

    print(bybit_exchange._exchange.timeframes)
    print(await bybit_exchange.fetch_ohlcv('BTC/USDT', timeframe='1m'))
    await bybit_exchange.close()




    # manager = EventManager()
    # manager.start()
    #
    # # Create and add some events with different priorities
    # event1 = Event(event_type=EventType.MARKET, priority=Priority.HIGH)
    # event2 = Event(event_type=EventType.ORDER, priority=Priority.LOW, metadata={"order_id": 123})
    # event3 = Event(event_type=EventType.SIGNAL, priority=Priority.MEDIUM)
    # event4 = Event(event_type=EventType.ERROR, priority=Priority.HIGH, metadata={"error_code": 500})
    #
    # manager.add_event(event1)
    # manager.add_event(event2)
    # manager.add_event(event3)
    # manager.add_event(event4)
    #
    # # Let the manager process events for a bit
    # time.sleep(2)
    #
    # manager.stop()


if __name__ == "__main__":
    asyncio.run(main())

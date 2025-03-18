import asyncio
import os
import db.db_connection as db

from dotenv import load_dotenv

from src.connectors.bybit_connector import BybitAsyncConnector


async def main():
    """
    Entry point for the application.
    Demonstrates how to use the EventManager to add and process events.

    :return: None
    """

    load_dotenv()
    bybit_exchange = BybitAsyncConnector(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'),
                                         testnet=True)

    await bybit_exchange.create_buy_order('72f8c4fd-562a-4fee-8d5a-7081a443733d')

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

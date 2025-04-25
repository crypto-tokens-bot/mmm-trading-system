PY = venv\Scripts\python.exe
MANAGE = -m src.manage
ENV = set "PYTHONPATH=." &
RUN = $(ENV) $(PY) $(MANAGE)

.PHONY: help \
        init list_event_managers create_event_manager remove_event_manager \
        list_strategies create_strategy remove_strategy \
        list_portfolios create_portfolio remove_portfolio \
        list_subscriptions create_subscription remove_subscription

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "init                     – apply migrations"
	@echo "list_event_managers      – show event managers"
	@echo "create_event_manager     – hard-coded example (edit before run)"
	@echo "remove_event_manager     – hard-coded example"
	@echo "… etc."

init:
	$(RUN) init

list_event_managers:
	$(RUN) list_event_managers

create_event_manager:
	$(RUN) create_event_manager --mode live

remove_event_manager:
	$(RUN) remove_event_manager --id 023a8284-6971-4012-bb46-374af747536f

list_strategies:
	$(RUN) list_strategies

create_strategy:
	$(RUN) create_strategy \
	  --event-manager-id fa9c3564-8674-4783-b495-d92eee939f4c \
	  --trading-pair BTC/USDT \
	  --strategy-name live_strategy \
	  --strategy-type Random \
	  --parameters "{\"timeframe\":\"1h\"}"

remove_strategy:
	$(RUN) remove_strategy --id 4672c7d8-644a-47f4-a8da-ce72194baca8

list_portfolios:
	$(RUN) list_portfolios

create_portfolio:
	$(RUN) create_portfolio \
	  --event-manager-id fa9c3564-8674-4783-b495-d92eee939f4c \
	  --risk-model simple \
	  --stop-loss-coefficient 0 \
	  --take-profit-coefficient 0 \
	  --max-asset-share "{\"BTC\":0.5,\"ETH\":0}" \
	  --portfolio-name my-portfolio1 \
	  --managed-assets "{\"BTC\":0,\"ETH\":0,\"USDT\":15000}" \
	  --initial-balance 150000 \
	  --currency USDT \
	  --exchange bybit

remove_portfolio:
	$(RUN) remove_portfolio --id 21ff530a-b852-49c6-9348-ef7cbd05e87e
# ----- subscriptions ------------------------------------------------------
list_subscriptions:
	$(RUN) list_subscriptions

create_subscription:
	$(RUN) create_subscription \
	  --portfolio-id 99e15af5-4701-4451-9d03-8030b722e2a2 \
	  --strategy-id  2e70dfe9-99e0-417d-aa8d-55be4d5e9823

remove_subscription:
	$(RUN) remove_subscription \
	  --portfolio-id 99e15af5-4701-4451-9d03-8030b722e2a2 \
	  --strategy-id  4672c7d8-644a-47f4-a8da-ce72194baca8

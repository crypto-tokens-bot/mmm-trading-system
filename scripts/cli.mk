PY = ..\venv\Scripts\python.exe
MANAGE = -m src.manage
ENV = set "PYTHONPATH=../" &
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
	  --event-manager-id b39602cb-136d-43c9-94d5-4b704d7360e0 \
	  --trading-pair BTC/USDT \
	  --strategy-name mean-reversion \
	  --strategy-type Random \
	  --parameters "{\"timeframe\":\"1d\"}"

remove_strategy:
	$(RUN) remove_strategy --id c824c96b-d255-467e-9e76-44d20ab170d6

list_portfolios:
	$(RUN) list_portfolios

create_portfolio:
	$(RUN) create_portfolio \
	  --event-manager-id b39602cb-136d-43c9-94d5-4b704d7360e0 \
	  --risk-model simple \
	  --stop-loss-coefficient 0.02 \
	  --take-profit-coefficient 0.05 \
	  --max-asset-share "{\"BTC\":0.5,\"ETH\":0.3,\"USDT\":1}" \
	  --portfolio-name my-portfolio3 \
	  --managed-assets "{\"BTC\":1,\"ETH\":2,\"USDT\":150000}" \
	  --initial-balance 150000 \
	  --currency USDT \
	  --exchange bybit

remove_portfolio:
	$(RUN) remove_portfolio --id 45531be8-0e15-4587-a691-c3e5c9c5490c
# ----- subscriptions ------------------------------------------------------
list_subscriptions:
	$(RUN) list_subscriptions

create_subscription:
	$(RUN) create_subscription \
	  --portfolio-id 850710bd-915e-49b4-82e5-a86f463be6b3 \
	  --strategy-id  7fc1fe7b-79b5-4c87-9ca2-cc544c2a8463

remove_subscription:
	$(RUN) remove_subscription \
	  --portfolio-id 5f47ac3d-8d84-4b77-9a51-2f4b8c9e2a6f \
	  --strategy-id  d290f1ee-6c54-4b01-90e6-d701748f0851

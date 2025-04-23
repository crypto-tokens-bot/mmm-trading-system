PY = ..\venv\Scripts\python.exe
MANAGE = -m src.manage
ENV = set "PYTHONPATH=../" &
RUN = $(ENV) $(PY) $(MANAGE)

.PHONY: help \
        init list_event_managers create_event_manager remove_event_manager \
        list_strategies create_strategy remove_strategy \
        list_portfolios create_portfolio remove_portfolio \
        list_subscriptions create_subscription remove_subscription

# ----- meta ---------------------------------------------------------------
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "init                     – apply migrations"
	@echo "list_event_managers      – show event managers"
	@echo "create_event_manager     – hard-coded example (edit before run)"
	@echo "remove_event_manager     – hard-coded example"
	@echo "… etc."
# ----- database -----------------------------------------------------------
init:
	$(RUN) init
# ----- event managers -----------------------------------------------------
list_event_managers:
	$(RUN) list_event_managers

create_event_manager:
	$(RUN) create_event_manager --mode live

remove_event_manager:
	$(RUN) remove_event_manager --id 703c868c-8570-4b60-bfa6-b8337bd49dbc

list_strategies:
	$(RUN) list_strategies

create_strategy:
	$(RUN) create_strategy \
	  --event-manager-id fa9c3564-8674-4783-b495-d92eee939f4c \
	  --trading-pair BTC/USDT \
	  --strategy-name mean-reversion \
	  --strategy-type momentum \
	  --parameters "{\"window\":20,\"threshold\":0.01}"

remove_strategy:
	$(RUN) remove_strategy --id d290f1ee-6c54-4b01-90e6-d701748f0851 --yes

list_portfolios:
	$(RUN) list_portfolios

create_portfolio:
	$(RUN) create_portfolio \
	  --event-manager-id fa9c3564-8674-4783-b495-d92eee939f4c \
	  --risk-model simple \
	  --stop-loss-coefficient 0.02 \
	  --take-profit-coefficient 0.05 \
	  --max-asset-share "{\"BTC\":0.5,\"ETH\":0.3,\"USDT\":0.2}" \
	  --portfolio-name my-portfolio3 \
	  --managed-assets "{\"BTC\":1,\"ETH\":2,\"USDT\":150000}" \
	  --initial-balance 100000 \
	  --currency USDT \
	  --exchange bybit

remove_portfolio:
	$(RUN) remove_portfolio --id 10032a58-5e95-4899-b4a5-38b8e01684e2
# ----- subscriptions ------------------------------------------------------
list_subscriptions:
	$(RUN) list_subscriptions

create_subscription:
	$(RUN) create_subscription \
	  --portfolio-id 5f47ac3d-8d84-4b77-9a51-2f4b8c9e2a6f \
	  --strategy-id  d290f1ee-6c54-4b01-90e6-d701748f0851

remove_subscription:
	$(RUN) remove_subscription \
	  --portfolio-id 5f47ac3d-8d84-4b77-9a51-2f4b8c9e2a6f \
	  --strategy-id  d290f1ee-6c54-4b01-90e6-d701748f0851

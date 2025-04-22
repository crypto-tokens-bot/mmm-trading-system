import json
import click

from src.db.queries.event_managers import get_all_event_managers, delete_event_manager, add_event_manager, \
    get_event_manager_by_id
from src.db.queries.portfolios import get_all_portfolios, delete_portfolio
from src.db.queries.strategies import get_all_strategies, delete_strategy, add_strategy
from src.monitoring import Monitoring


@click.group()
def cli():
    """CLI for managing strategies and portfolios via query modules"""
    pass

@cli.command('init')
def init_db():
    """Apply migrations using migrate.py's apply_migrations function."""
    from src.db.migrations.migrate import apply_migrations
    apply_migrations()
    click.echo("Migrations applied successfully.")


@cli.command('list_event_managers')
def list_event_managers():
    """List all event managers for selection."""
    result = get_all_event_managers()
    for event_manager in result:
        attrs = ", ".join(f"{key}={value}" for key, value in event_manager.items())
        click.echo(f"- {attrs}")


@cli.command('list_strategies')
def list_strategies():
    """List all strategies using attributes from the table schema."""
    result = get_all_strategies()
    for strategy in result:
        attrs = ", ".join(f"{key}={value}" for key, value in strategy.items())
        click.echo(f"- {attrs}")


@cli.command('list_portfolios')
def list_portfolios():
    """List all portfolios using attributes from the table schema."""
    result = get_all_portfolios()
    for portfolio in result:
        attrs = ", ".join(f"{key}={value}" for key, value in portfolio.items())
        click.echo(f"- {attrs}")


@cli.command('remove_strategy')
@click.option('--id', 'strategy_id', required=True, type=str,
              help='Strategy UUID to delete')
@click.option('-y', '--yes', is_flag=True,
              help='Confirm without prompt')
def remove_strategy(strategy_id, yes):
    """Remove a strategy by UUID."""
    if not yes and not click.confirm(f"Delete strategy id={strategy_id}? "):
        click.echo("Aborted.")
        return

    delete_strategy(strategy_id)
    click.echo(f"Strategy id={strategy_id} deleted.")


@cli.command('remove_portfolio')
@click.option('--id', 'portfolio_id', required=True, type=str,
              help='Portfolio UUID to delete')
@click.option('-y', '--yes', is_flag=True,
              help='Confirm without prompt')
def remove_portfolio(portfolio_id, yes):
    """Remove a portfolio by UUID."""
    if not yes and not click.confirm(f"Delete portfolio id={portfolio_id}? "):
        click.echo("Aborted.")
        return

    delete_portfolio(portfolio_id)
    click.echo(f"Portfolio id={portfolio_id} deleted.")


@cli.command('remove_event_manager')
@click.option('--id', 'event_manager_id', required=True, type=str,
              help='Event Manager UUID to delete')
@click.option('-y', '--yes', is_flag=True,
              help='Confirm without prompt')
def remove_event_manager(event_manager_id, yes):
    """Remove an event manager by UUID."""
    if not yes and not click.confirm(f"Delete event manager id={event_manager_id}? "):
        click.echo("Aborted.")
        return

    delete_event_manager(event_manager_id)
    click.echo(f"Event manager id={event_manager_id} deleted.")


@cli.command('create_event_manager')
@click.option(
    '--mode',
    type=click.Choice(['live', 'backtest'], case_sensitive=False),
    required=True,
    help='Mode of the event manager (live or backtest)'
)
def create_event_manager(mode):
    """Add a new event manager in inactive status by default."""
    new_id = add_event_manager(mode=mode, status='inactive')
    click.echo(f"Event manager (mode={mode}, status=inactive) added with id={new_id}.")


@cli.command('create_strategy')
@click.option(
    '--event-manager-id', 'event_manager_id', required=True,
    help='UUID of the existing event manager'
)
@click.option(
    '--trading-pair', required=True,
    help='Trading pair for this strategy (e.g., BTC/USDT)'
)
@click.option(
    '--strategy-name', 'strategy_name', required=True,
    help='Name of the strategy'
)
@click.option(
    '--strategy-type', 'strategy_type', required=True,
    help='Type of the strategy'
)
@click.option(
    '--parameters', 'parameters_json', required=True,
    help='Strategy parameters as JSON string'
)
def create_strategy(event_manager_id, trading_pair, strategy_name, strategy_type, parameters_json):
    """Add a new strategy under an existing event manager."""
    #  $env:PYTHONPATH = "."; python -m src.manage create_strategy --event-manager-id 023a8284-6971-4012-bb46-374af747536f --trading-pair BTC/USDT --strategy-name Test --strategy-type Random --parameters '{}'
    try:
        params = json.loads(parameters_json)
    except json.JSONDecodeError:
        click.echo("Invalid JSON for parameters", err=True)
        raise click.Abort()

    try:
        event_manager = get_event_manager_by_id(event_manager_id)
        if event_manager is None:
            raise Exception
    except Exception:
        click.echo(f"Error: event_manager_id {event_manager_id} does not exist.", err=True)
        raise click.Abort()

    strategy_id = add_strategy(
        event_manager_id=event_manager_id,
        trading_pair=trading_pair,
        strategy_name=strategy_name,
        strategy_type=strategy_type,
        parameters=parameters_json
    )
    click.echo(f"Strategy '{strategy_name}' (type={strategy_type}) added with id={strategy_id}.")


@cli.command()
@click.option('--name', required=True,
              help='Unique portfolio name')
@click.option('--risk-params', 'risk_params_json', required=True,
              help='Risk controller params JSON')
def add_portfolio(name, risk_params_json):
    """Add a new portfolio."""
    try:
        json.loads(risk_params_json)
    except json.JSONDecodeError:
        click.echo("Invalid JSON for risk controller parameters", err=True)
        raise click.Abort()

    new_id = insert_portfolio(name=name, risk_controller_params=risk_params_json)
    click.echo(f"Portfolio '{name}' added with id={new_id}.")



if __name__ == '__main__':
    cli()


# При создании портфеля нужно также создать и риск контроллер, поэтому для него тоже запрашиваем параматеры
# add_portfolio(event_manager_id, risk_controller_id, portfolio_name, managed_assets, currency, initial_balance, exchange)
# add_risk_controller(risk_model, stop_loss_coefficient, take_profit_coefficient,  max_asset_share):
#
# event_manager_id должен существовать, portfolio_name должно быть уникально, managed_assets - json, currenct по умолчанию USDT, initial_balance, exchange по умолччанию bybit
# risk_model, stop_loss_coefficient по умолчанию None, take_profit_coefficient по умолчанию None, max_asset_share - json
#
# Сначала создаём риск контроллер, затем портфель, предварительно обязательно проверить корректность всех полей.


# Создать метод для добавления и удаления подписок портфелей на стратегии:
#     add_strategy_subscription(portfolio_id, strategy_id)
#     оба id должны существовать
#
# Метод для удаления необходимо реализовать


# В функции main необходимо запустить все event_managerы.
# Необходимо создать классы со стратегиями.
#
# Создать MarketDataProvider, подписать его на стратегии. Таймфреймы брать из параметров стратегии. Если там нет, то по умолчанию '1h'
# Создать Monitoring
#
# Необхоидмо создать классы для всех портфелей (параллельно создавай классы для риск контроллеров).
# Необходимо подписать портфели на стратегии, следуя таблице strategy_subscriptions
#
# Далее ожидаем завершения программы
#
# Перед завершением ожидать окончания работы всех классов.

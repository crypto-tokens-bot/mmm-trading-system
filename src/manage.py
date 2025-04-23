import json
import click

from src.db.queries.event_managers import get_all_event_managers, delete_event_manager, add_event_manager, \
    get_event_manager_by_id
from src.db.queries.portfolios import get_all_portfolios, delete_portfolio, add_portfolio
from src.db.queries.risk_controllers import add_risk_controller
from src.db.queries.strategies import get_all_strategies, delete_strategy, add_strategy
from src.db.queries.strategy_subscriptions import add_strategy_subscription, delete_strategy_subscription, \
    get_all_subscriptions
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


@cli.command('list_subscriptions')
def list_subscriptions():
    """List all portfolios using attributes from the table schema."""
    result = get_all_subscriptions()
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
    #  $env:PYTHONPATH = "."; python -m src.manage create_strategy --event-manager-id 023a8284-6971-4012-bb46-374af747536f --trading-pair BTC/USDT --strategy-name Test --strategy-type Random --parameters '{\"window\":20,\"threshold\":0.01}'
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


@cli.command('create_portfolio')
@click.option('--event-manager-id','event_manager_id', required=True, help='UUID of the existing event manager')
@click.option('--risk-model', 'risk_model', default=None, help='Risk model name')
@click.option('--stop-loss-coefficient', 'stop_loss_coefficient', type=float, default=None, help='Stop loss coefficient (optional)')
@click.option('--take-profit-coefficient', 'take_profit_coefficient', type=float, default=None, help='Take profit coefficient (optional)')
@click.option('--max-asset-share', 'max_asset_share_json', required=True, help='Max asset share JSON')
@click.option('--portfolio-name','portfolio_name', required=True, help='Portfolio name (unique)')
@click.option('--managed-assets', 'managed_assets_json', required=True, help='Managed assets JSON')
@click.option('--currency', default='USDT', show_default=True, help='Currency')
@click.option('--initial-balance', 'initial_balance', type=float, required=True, help='Initial balance')
@click.option('--exchange', default='bybit', show_default=True, help='Exchange name')
def create_portfolio(event_manager_id, risk_model, stop_loss_coefficient,
                     take_profit_coefficient, max_asset_share_json,
                     portfolio_name, managed_assets_json,
                     currency, initial_balance, exchange):
    """Create a new portfolio with associated risk controller."""
    # python src/manage.py create_portfolio --event-manager-id 023a8284-6971-4012-bb46-374af747536f --risk-model simple --stop-loss-coefficient 0.5 --take-profit-coefficient 1.5 --max-asset-share '{\"BTC\":0.5,\"ETH\":0.3,\"USDT\":0.2}' --portfolio-name my-portfolio2 --managed-assets '{\"BTC\": 1,\"ETH\": 2,\"USDT\": 150000}' --initial-balance 15000 --currency USDT --exchange bybit
    try:
        managed_assets_json = json.loads(managed_assets_json)
        max_asset_share_json = json.loads(max_asset_share_json)
    except json.JSONDecodeError:
        click.echo("Invalid JSON for managed assets or max asset share", err=True)
        raise click.Abort()

    try:
        event_manager = get_event_manager_by_id(event_manager_id)
        if event_manager is None:
            raise Exception
    except Exception:
        click.echo(f"Error: event_manager_id {event_manager_id} does not exist.", err=True)
        raise click.Abort()

    portfolios = get_all_portfolios()
    if portfolio_name in {p['portfolio_name'] for p in portfolios}:
        click.echo(f"Error: portfolio name '{portfolio_name}' already exists", err=True)
        raise click.Abort()

    risk_controller_id = add_risk_controller(
        risk_model=risk_model,
        stop_loss_coefficient=stop_loss_coefficient,
        take_profit_coefficient=take_profit_coefficient,
        max_asset_share=max_asset_share_json
    )

    portfolio_id = add_portfolio(
        event_manager_id=event_manager_id,
        risk_controller_id=risk_controller_id,
        portfolio_name=portfolio_name,
        managed_assets=managed_assets_json,
        currency=currency,
        initial_balance=initial_balance,
        exchange=exchange
    )
    click.echo(
        f"Portfolio created: id={portfolio_id}, name={portfolio_name}, rc_id={risk_controller_id}"
    )

@cli.command('create_subscription')
@click.option('--portfolio-id', 'portfolio_id', required=True, help='UUID of the portfolio')
@click.option('--strategy-id', 'strategy_id', required=True, help='UUID of the strategy')
def create_subscription(portfolio_id, strategy_id):
    """Subscribe a strategy to a portfolio."""
    if portfolio_id not in {str(p['portfolio_id']) for p in get_all_portfolios()}:
        click.echo(f"Error: portfolio_id {portfolio_id} not found", err=True)
        raise click.Abort()
    if strategy_id not in {str(s['strategy_id']) for s in get_all_strategies()}:
        click.echo(f"Error: strategy_id {strategy_id} not found", err=True)
        raise click.Abort()
    add_strategy_subscription(portfolio_id, strategy_id)
    click.echo(f"Subscription created: portfolio {portfolio_id} -> strategy {strategy_id}")

@cli.command('remove_subscription')
@click.option('--portfolio-id', 'portfolio_id', required=True, help='UUID of the portfolio')
@click.option('--strategy-id', 'strategy_id', required=True, help='UUID of the strategy')
def remove_subscription(portfolio_id, strategy_id):
    """Unsubscribe a strategy from a portfolio."""
    delete_strategy_subscription(portfolio_id, strategy_id)
    click.echo(f"Subscription removed: portfolio {portfolio_id} -> strategy {strategy_id}")



if __name__ == '__main__':
    cli()
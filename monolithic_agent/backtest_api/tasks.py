"""
Celery tasks for backtesting.

The view creates a BacktestRun record (status='queued'), then immediately
returns a job_id. This worker picks it up and does the heavy computation.
Poll GET /api/jobs/<task_id>/ to track progress and retrieve the result.
"""
import logging
import traceback

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='backtest_api.tasks.run_backtest')
def run_backtest_task(self, run_id: str, backtest_params: dict):
    """
    Execute a backtest in a Celery worker.

    `run_id` is the BacktestRun.run_id already created by the view.
    """
    from backtest_api.models import BacktestRun, BacktestResult

    try:
        run = BacktestRun.objects.get(run_id=run_id)
        run.status = 'running'
        run.started_at = timezone.now()
        run.save()

        self.update_state(state='PROGRESS', meta={'step': 'Running backtest', 'run_id': run_id, 'pct': 10})

        from Backtest.interactive_backtest_runner import InteractiveBacktestRunner
        runner = InteractiveBacktestRunner()
        result = runner.run_backtest(backtest_params)

        if result.get('success', False):
            metrics = result.get('metrics', {})
            initial_capital = backtest_params.get('initial_capital', 10000)

            backtest_result = BacktestResult.objects.create(
                run=run,
                final_portfolio_value=metrics.get('final_portfolio_value', initial_capital),
                total_return_pct=metrics.get('total_return', 0),
                annualized_return_pct=metrics.get('annualized_return', 0),
                volatility=metrics.get('volatility', 0),
                sharpe_ratio=metrics.get('sharpe_ratio', 0),
                max_drawdown_pct=metrics.get('max_drawdown', 0),
                max_drawdown_duration=metrics.get('max_drawdown_duration', 0),
                current_drawdown_pct=metrics.get('current_drawdown', 0),
                total_trades=metrics.get('total_trades', 0),
                winning_trades=metrics.get('winning_trades', 0),
                losing_trades=metrics.get('losing_trades', 0),
                win_rate_pct=metrics.get('win_rate', 0),
                avg_trade_return_pct=metrics.get('avg_trade_return', 0),
                avg_winning_trade_pct=metrics.get('avg_winning_trade', 0),
                avg_losing_trade_pct=metrics.get('avg_losing_trade', 0),
                largest_winning_trade_pct=metrics.get('largest_winning_trade', 0),
                largest_losing_trade_pct=metrics.get('largest_losing_trade', 0),
                profit_factor=metrics.get('profit_factor', 0),
                payoff_ratio=metrics.get('payoff_ratio', 0),
                portfolio_values=result.get('portfolio_values', {}),
                returns=result.get('returns', {}),
                drawdowns=result.get('drawdowns', {}),
                positions=result.get('positions', {}),
            )

            run.status = 'completed'
            run.completed_at = timezone.now()
            run.execution_time = (run.completed_at - run.started_at).total_seconds()
            run.total_return = backtest_result.total_return_pct
            run.sharpe_ratio = backtest_result.sharpe_ratio
            run.max_drawdown = backtest_result.max_drawdown_pct
            run.total_trades = backtest_result.total_trades
            run.win_rate = backtest_result.win_rate_pct
            run.save()

            return {
                'run_id': run.run_id,
                'status': 'completed',
                'result_summary': {
                    'total_return': float(backtest_result.total_return_pct),
                    'sharpe_ratio': float(backtest_result.sharpe_ratio),
                    'max_drawdown': float(backtest_result.max_drawdown_pct),
                    'total_trades': backtest_result.total_trades,
                    'win_rate': float(backtest_result.win_rate_pct),
                },
            }

        else:
            error_msg = result.get('error', 'Unknown error')
            run.status = 'failed'
            run.completed_at = timezone.now()
            run.error_message = error_msg
            run.save()
            raise RuntimeError(error_msg)

    except BacktestRun.DoesNotExist:
        logger.error(f"[Task] BacktestRun {run_id} not found")
        raise
    except Exception as exc:
        logger.error(f"[Task] run_backtest_task failed for run {run_id}: {exc}")
        logger.error(traceback.format_exc())
        # Try to mark run as failed in DB
        try:
            run = BacktestRun.objects.get(run_id=run_id)
            run.status = 'failed'
            run.error_message = str(exc)
            run.completed_at = timezone.now()
            run.save()
        except Exception:
            pass
        raise

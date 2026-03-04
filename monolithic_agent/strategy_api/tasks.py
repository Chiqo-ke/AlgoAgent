"""
Celery tasks for strategy generation.

These run inside a dedicated Celery worker process, so the HTTP server
threads are freed up immediately — multiple users can generate strategies
in parallel without any request blocking another.
"""
import logging
import os
import traceback

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='strategy_api.tasks.generate_strategy')
def generate_strategy_task(
    self,
    description: str,
    auto_fix: bool = True,
    execute_after: bool = False,
    max_fix_attempts: int = 8,
    user_id=None,
):
    """
    AI strategy generation — runs in Celery worker.

    Poll GET /api/jobs/<task_id>/ to track progress and retrieve the result.
    """
    try:
        self.update_state(state='PROGRESS', meta={'step': 'Initialising generator', 'pct': 5})

        # Prefer GitHub Copilot generator, fall back to Gemini
        try:
            from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
            generator = CopilotStrategyGenerator()
            logger.info("[Task] Using GitHub Copilot generator")
        except Exception:
            from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
            generator = GeminiStrategyGenerator()
            logger.info("[Task] Using Gemini generator")

        self.update_state(state='PROGRESS', meta={'step': 'Generating strategy code', 'pct': 20})

        output_file, execution_result = generator.generate_and_save(
            description=description,
            execute_after_generation=execute_after,
        )

        fix_history = []
        if auto_fix and execution_result and not execution_result.success:
            self.update_state(state='PROGRESS', meta={'step': 'Auto-fixing errors', 'pct': 50})
            logger.info(f"[Task] Auto-fixing strategy errors for {output_file}")
            success, final_path, fix_history = generator.fix_bot_errors_iteratively(
                strategy_file=output_file,
                max_iterations=max_fix_attempts,
            )
            if success:
                from Backtest.bot_executor import BotExecutor
                executor = BotExecutor()
                execution_result = executor.execute_bot(strategy_file=final_path)
                output_file = final_path

        self.update_state(state='PROGRESS', meta={'step': 'Saving to database', 'pct': 90})

        from strategy_api.models import Strategy
        from django.contrib.auth import get_user_model

        user = None
        if user_id:
            try:
                user = get_user_model().objects.get(id=user_id)
            except Exception:
                pass

        strategy_name = os.path.basename(output_file).replace('.py', '')
        run_status = 'generated'
        if execution_result:
            run_status = 'executed' if execution_result.success else 'failed'

        strategy = Strategy.objects.create(
            name=strategy_name,
            description=description,
            strategy_code='',
            file_path=output_file,
            status=run_status,
            created_by=user,
        )

        return {
            'id': strategy.id,
            'name': strategy.name,
            'file_path': output_file,
            'status': strategy.status,
            'generation_result': {'success': True, 'file_path': output_file},
            'execution_result': {
                'success': execution_result.success,
                'return_pct': execution_result.return_pct,
                'num_trades': execution_result.num_trades,
                'win_rate': execution_result.win_rate,
                'sharpe_ratio': execution_result.sharpe_ratio,
                'max_drawdown': execution_result.max_drawdown,
            } if execution_result else None,
            'fix_attempts': len(fix_history),
            'fix_details': [
                {'attempt': i + 1, 'error_type': a.error_type, 'success': a.success}
                for i, a in enumerate(fix_history)
            ],
        }

    except Exception as exc:
        logger.error(f"[Task] generate_strategy_task failed: {exc}")
        logger.error(traceback.format_exc())
        raise  # Celery marks task as FAILURE and stores the exception

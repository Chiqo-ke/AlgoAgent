"""
Generic job-status endpoint — works for any Celery task.

GET /api/jobs/<task_id>/

Possible states returned by Celery:
  PENDING  — task not yet picked up (or unknown task id)
  STARTED  — worker has started the task
  PROGRESS — task is running and has sent a progress update
  SUCCESS  — task finished successfully; result contains the return value
  FAILURE  — task raised an exception; error contains the message
  REVOKED  — task was cancelled
"""
from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def job_status(request, task_id: str):
    result = AsyncResult(task_id)

    state = result.state   # str
    info = result.info     # meta dict (PROGRESS), exception (FAILURE), or return value (SUCCESS)

    if state == 'PENDING':
        data = {
            'job_id': task_id,
            'state': 'PENDING',
            'progress': None,
            'result': None,
            'error': None,
        }
    elif state == 'PROGRESS':
        data = {
            'job_id': task_id,
            'state': 'PROGRESS',
            'progress': info,
            'result': None,
            'error': None,
        }
    elif state == 'SUCCESS':
        data = {
            'job_id': task_id,
            'state': 'SUCCESS',
            'progress': None,
            'result': result.get(),
            'error': None,
        }
    elif state == 'FAILURE':
        data = {
            'job_id': task_id,
            'state': 'FAILURE',
            'progress': None,
            'result': None,
            'error': str(info),
        }
    else:
        data = {
            'job_id': task_id,
            'state': state,
            'progress': info if isinstance(info, dict) else None,
            'result': None,
            'error': None,
        }

    return JsonResponse(data)

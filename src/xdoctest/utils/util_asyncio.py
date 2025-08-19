"""
Utilities related to async support
"""
import asyncio
import sys


# see asyncio.runners.Runner
class FallbackRunner:
    """A fallback implementation of :class:`asyncio.Runner` for Python<3.11."""

    def __init__(self):
        self._loop = None

    def run(self, coro):
        """
        Run code in the embedded event loop.

        Example:
            >>> import asyncio
            >>> async def test():
            >>>     return asyncio.sleep(0, result='slept')
            >>> runner = FallbackRunner()
            >>> try:
            >>>     task = runner.run(test())
            >>>     result = runner.run(task)
            >>> finally:
            >>>     runner.close()
            >>> result
            'slept'

        Example:
            >>> import asyncio
            >>> runner = FallbackRunner()
            >>> try:
            >>>     runner.run(asyncio.sleep(0))  # xdoctest: +ASYNC
            >>> finally:
            >>>     runner.close()
            Traceback (most recent call last):
            RuntimeError: Runner.run() cannot be called from a running event loop
        """
        if running():
            msg = 'Runner.run() cannot be called from a running event loop'
            raise RuntimeError(msg)
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)

    def close(self):
        """
        Shutdown and close event loop.

        Example:
            >>> import asyncio
            >>> runner = FallbackRunner()
            >>> try:
            >>>     runner.run(asyncio.sleep(0))
            >>> finally:
            >>>     runner.close()
            >>> runner.close()  # must be no-op

        Example:
            >>> import asyncio
            >>> async def main():
            >>>     global task  # avoid disappearing
            >>>     task = asyncio.create_task(asyncio.sleep(3600))
            >>>     await asyncio.sleep(0)  # start the task
            >>> runner = FallbackRunner()
            >>> try:
            >>>     runner.run(main())
            >>> finally:
            >>>     runner.close()
            >>> task.cancelled()
            True

        Example:
            >>> import asyncio
            >>> def handler(loop, context):
            >>>     global exc_context
            >>>     exc_context = context
            >>> async def test():
            >>>     asyncio.get_running_loop().set_exception_handler(handler)
            >>>     try:
            >>>         await asyncio.sleep(3600)
            >>>     except asyncio.CancelledError:
            >>>         1 // 0  # raise ZeroDivisionError
            >>> async def main():
            >>>     global task  # avoid disappearing
            >>>     task = asyncio.create_task(test())
            >>>     await asyncio.sleep(0)  # start the task
            >>> runner = FallbackRunner()
            >>> try:
            >>>     runner.run(main())
            >>> finally:
            >>>     runner.close()
            >>> exc_context['message']
            'unhandled exception during asyncio.run() shutdown'
            >>> isinstance(exc_context['exception'], ZeroDivisionError)
            True
            >>> exc_context['task'] is task
            True
        """
        loop = self._loop
        if loop is None:
            return
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
            if sys.version_info >= (3, 9):
                loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            asyncio.set_event_loop(None)
            loop.close()
            self._loop = None


# see asyncio.runners._cancel_all_tasks
def _cancel_all_tasks(loop):
    to_cancel = asyncio.all_tasks(loop)
    if not to_cancel:
        return
    for task in to_cancel:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*to_cancel, return_exceptions=True))
    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })


def running():
    """
    Return :data:`True` if there is a running event loop.

    Example:
        >>> running()  # xdoctest: +ASYNC
        True
        >>> running()  # xdoctest: -ASYNC
        False
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # no running event loop
        loop = None

    return loop is not None


if sys.version_info >= (3, 11):
    from asyncio import Runner
else:
    Runner = FallbackRunner

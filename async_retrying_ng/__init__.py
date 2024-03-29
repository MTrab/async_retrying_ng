"""Async retry module."""
import asyncio
import copy
import inspect
import logging
from functools import wraps
import random

import async_timeout

logger = logging.getLogger(__name__)


propagate = forever = ...


class RetryError(Exception):
    """Raised when retry attempts has been exceeded."""


class ConditionError(Exception):
    """Raised when an conditional error occurs."""


def unpartial(fn):
    while hasattr(fn, "func"):
        fn = fn.func

    return fn


def isexception(obj):
    return isinstance(obj, Exception) or (
        inspect.isclass(obj) and (issubclass(obj, Exception))
    )


async def callback(attempt, exc, args, kwargs, delay=None, *, loop):
    if delay is None:
        delay = getattr(callback, "delay", 0.5)

    await asyncio.sleep(attempt * delay)

    return retry


def retry(
    fn=None,
    *,
    attempts=3,
    delay=0.5,
    max_delay=None,
    backoff=1,
    jitter=0,
    immutable=False,
    cls=False,
    kwargs=False,
    callback=callback,
    fallback=RetryError,
    timeout=None,
    retry_exceptions=(Exception,),
    fatal_exceptions=(asyncio.CancelledError,),
    loop=None  # noqa
):
    def wrapper(fn):
        @wraps(fn)
        async def wrapped(*fn_args, **fn_kwargs):
            if isinstance(loop, str):
                assert cls ^ kwargs, 'choose self.loop or kwargs["loop"]'

                if cls:
                    _self = getattr(unpartial(fn), "__self__", None)

                    if _self is None:
                        assert fn_args, "seems not unbound function"
                        _self = fn_args[0]

                    _loop = getattr(_self, loop)
                elif kwargs:
                    _loop = fn_kwargs[loop]
            elif loop is None:
                _loop = asyncio.get_running_loop()
            else:
                _loop = loop

            if timeout is not None and asyncio.TimeoutError not in retry_exceptions:
                _retry_exceptions = (asyncio.TimeoutError,) + retry_exceptions
            else:
                _retry_exceptions = retry_exceptions

            attempt = 1
            _delay = delay

            if cls:
                assert fn_args

                self, *fn_args = fn_args

                fn_args = tuple(fn_args)

            while True:
                if immutable:
                    _fn_args = copy.deepcopy(fn_args)

                    kwargs_loop = isinstance(loop, str) and kwargs

                    if kwargs_loop:
                        obj = fn_kwargs.pop(loop)

                    _fn_kwargs = copy.deepcopy(fn_kwargs)

                    if kwargs_loop:
                        fn_kwargs[loop] = _fn_kwargs[loop] = obj
                else:
                    _fn_args, _fn_kwargs = fn_args, fn_kwargs

                if cls:
                    _fn_args = (self,) + _fn_args

                try:
                    ret = fn(*_fn_args, **_fn_kwargs)

                    if timeout is None:
                        if asyncio.iscoroutinefunction(unpartial(fn)):
                            ret = await ret
                    else:
                        if not asyncio.iscoroutinefunction(unpartial(fn)):
                            raise ConditionError(
                                "Can't set timeout for non coroutinefunction",
                            )

                        # Note no async_timeout shortcuts here
                        # because we must keep a loop passed from the outside.
                        async with async_timeout.Timeout(
                            _loop.time() + timeout,
                            loop=_loop,
                        ):
                            ret = await ret

                    return ret

                except ConditionError:
                    raise
                except fatal_exceptions:
                    raise
                except _retry_exceptions as exc:
                    _attempts = "infinity" if attempts is forever else attempts
                    context = {
                        "fn": fn,
                        "attempt": attempt,
                        "attempts": _attempts,
                    }

                    if attempts is not forever and attempt == attempts:
                        logger.warning(
                            exc.__class__.__name__
                            + " -> Attempts (%(attempt)d) are over for %(fn)r",  # noqa
                            context,
                            exc_info=exc,
                        )
                        if fallback is propagate:
                            raise exc

                        if isexception(fallback):
                            raise fallback from exc

                        if callable(fallback):
                            ret = fallback(fn_args, fn_kwargs, loop=_loop)

                            if asyncio.iscoroutinefunction(unpartial(fallback)):  # noqa
                                ret = await ret
                        else:
                            ret = fallback

                        return ret

                    logger.debug(
                        exc.__class__.__name__
                        + " -> Tried attempt #%(attempt)d from total %(attempts)s for %(fn)r",  # noqa
                        context,
                        exc_info=exc,
                    )

                    ret = callback(
                        attempt,
                        exc,
                        fn_args,
                        fn_kwargs,
                        delay=_delay,
                        loop=_loop,
                    )

                    _delay *= backoff
                    if isinstance(jitter, tuple):
                        _delay += random.uniform(*jitter)
                    else:
                        _delay += jitter
                    if max_delay is not None:
                        _delay = min(_delay, max_delay)

                    attempt += 1

                    if asyncio.iscoroutinefunction(unpartial(callback)):
                        ret = await ret

                    if ret is not retry:
                        return ret

        return wrapped

    if fn is None:
        return wrapper

    if callable(fn):
        return wrapper(fn)

    raise NotImplementedError

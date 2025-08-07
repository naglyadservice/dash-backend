import functools
import inspect
from collections.abc import Callable
from datetime import datetime
from inspect import Parameter
from typing import Awaitable, ParamSpec, TypeVar, get_type_hints

from adaptix import Retort, dumper, loader
from dishka import AsyncContainer, Scope
from dishka.integrations.base import wrap_injection

T = TypeVar("T")
P = ParamSpec("P")

datetime_recipe = (
    loader(datetime, lambda s: datetime.fromisoformat(s)),  # noqa: DTZ007
    dumper(datetime, lambda dt: dt.isoformat()),
)

default_retort = Retort(
    recipe=[
        *datetime_recipe,
    ]
)


def get_arg_type(func, position):
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    second_param = params[position].name
    hints = get_type_hints(func)
    return hints.get(second_param)


def parse_payload(retort: Retort | None = None):
    if retort is None:
        retort = default_retort

    def _parse_paylaad(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tp = get_arg_type(func, 1)

            data = retort.load(args[1], tp)
            args = list(args)
            args[1] = data

            return await func(*args, **kwargs)

        return wrapper

    return _parse_paylaad


def request_scope(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        di_container: AsyncContainer = kwargs["di_container"]  # type: ignore
        if di_container.scope is Scope.APP:
            async with di_container(scope=Scope.REQUEST) as container:
                kwargs["di_container"] = container
                return await func(*args, **kwargs)
        else:
            return await func(*args, **kwargs)

    return wrapper


def inject(func: Callable[P, T]) -> Callable[P, T]:
    return wrap_injection(
        func=func,
        is_async=True,
        container_getter=lambda _, p: p["di_container"],
        additional_params=[
            Parameter(
                name="di_container",
                annotation=AsyncContainer,
                kind=Parameter.KEYWORD_ONLY,
            ),
        ],
    )

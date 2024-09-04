from collections.abc import Awaitable
from typing import Callable, Optional, TypeVar

from nonebot import on_notice
from nonebot.adapters import Bot, Event

from .receipt import Receipt

B = TypeVar("B", bound=Bot)
E = TypeVar("E", bound=Event)
R = TypeVar("R", bound=Receipt)


WithdrawFunction = Callable[[B, R], Awaitable[None]]

_withdraw_functions: dict[type[Bot], WithdrawFunction] = {}


def register_withdraw_function(bot: type[Bot]):
    def wrapper(func: WithdrawFunction):
        _withdraw_functions[bot] = func

    return wrapper


ReceiptExtractor = Callable[[B, E], Awaitable[Optional[R]]]

_receipt_extractors: dict[type[Event], ReceiptExtractor] = {}


def register_receipt_extractor(event: type[Event]):
    def wrapper(func: ReceiptExtractor):
        _receipt_extractors[event] = func

    return wrapper


async def withdraw_message(bot: Bot, receipt: Receipt):
    for bot_type, func in _withdraw_functions.items():
        if isinstance(bot, bot_type):
            return await func(bot, receipt)


async def extract_receipt(bot: Bot, event: Event) -> Optional[Receipt]:
    for event_type, extractor in _receipt_extractors.items():
        if isinstance(event, event_type):
            return await extractor(bot, event)


withdraw_notice = on_notice()

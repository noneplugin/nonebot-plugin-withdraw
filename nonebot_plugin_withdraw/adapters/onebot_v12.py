from contextlib import suppress
from typing import Any, Optional, Union

from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_session import EventSession, Session, SessionIdType, SessionLevel

from ..handler import (
    register_receipt_extractor,
    register_withdraw_function,
    withdraw_notice,
)
from ..receipt import Receipt, add_receipt, remove_receipt

with suppress(ImportError):
    from nonebot.adapters.onebot.v12 import (
        Bot,
        GroupMessageDeleteEvent,
        MessageEvent,
        PrivateMessageDeleteEvent,
    )

    class OnebotV12Receipt(Receipt):
        message_id: str

        def get_id(self) -> str:
            return self.message_id

    @Bot.on_called_api
    async def _(
        bot: BaseBot,
        e: Optional[Exception],
        api: str,
        data: dict[str, Any],
        result: Any,
    ):
        if not isinstance(bot, Bot):
            return
        if e or not result:
            return

        if api not in ["send_message"]:
            return

        detail_type = data["detail_type"]
        level = SessionLevel.LEVEL0
        if detail_type == "channel":
            level = SessionLevel.LEVEL3
        elif detail_type == "group":
            level = SessionLevel.LEVEL2
        elif detail_type == "private":
            level = SessionLevel.LEVEL1

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=bot.platform,
            level=level,
            id1=data.get("user_id"),
            id2=data.get("group_id") or data.get("channel_id"),
            id3=data.get("guild_id"),
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = OnebotV12Receipt(message_id=result["message_id"])
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(
        event: Union[GroupMessageDeleteEvent, PrivateMessageDeleteEvent],
        session: EventSession,
    ):
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = OnebotV12Receipt(message_id=event.message_id)
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: OnebotV12Receipt):
        await bot.delete_message(message_id=receipt.message_id)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply:
            return OnebotV12Receipt(message_id=reply.message_id)

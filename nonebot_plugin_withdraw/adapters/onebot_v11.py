from contextlib import suppress
from typing import Any, Optional

from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_session import EventSession, Session, SessionIdType, SessionLevel
from nonebot_plugin_session.const import SupportedPlatform

from ..handler import (
    register_receipt_extractor,
    register_withdraw_function,
    withdraw_notice,
)
from ..receipt import Receipt, add_receipt, remove_receipt

with suppress(ImportError):
    from nonebot.adapters.onebot.v11 import Bot, GroupRecallNoticeEvent, MessageEvent

    class OnebotV11Receipt(Receipt):
        message_id: int

        def get_id(self) -> str:
            return str(self.message_id)

    @Bot.on_called_api
    async def _(
        bot: BaseBot,
        e: Optional[Exception],
        api: str,
        data: dict[str, Any],
        result: Any,
    ):
        if not isinstance(bot, Bot):
            return []
        if e or not result:
            return []

        if api in ["send_msg", "send_forward_msg"]:
            msg_type = data["message_type"]
            if msg_type == "group":
                level = level = SessionLevel.LEVEL2
            else:
                level = SessionLevel.LEVEL1
        elif api in ["send_private_msg", "send_private_forward_msg"]:
            level = SessionLevel.LEVEL1
        elif api in ["send_group_msg", "send_group_forward_msg"]:
            level = SessionLevel.LEVEL2
        else:
            return

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=SupportedPlatform.qq,
            level=level,
            id1=str(data.get("user_id", "")) or None,
            id2=str(data.get("group_id", "")) or None,
            id3=None,
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = OnebotV11Receipt(message_id=result["message_id"])
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(bot: Bot, event: GroupRecallNoticeEvent, session: EventSession):
        if str(event.user_id) != bot.self_id:
            return
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = OnebotV11Receipt(message_id=event.message_id)
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: OnebotV11Receipt):
        await bot.delete_msg(message_id=receipt.message_id)

    @register_receipt_extractor(MessageEvent)
    def _(event: MessageEvent):
        if reply := event.reply:
            return OnebotV11Receipt(message_id=reply.message_id)

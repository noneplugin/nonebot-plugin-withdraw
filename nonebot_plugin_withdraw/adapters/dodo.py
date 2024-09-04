from contextlib import suppress
from typing import Any, Optional

from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_session import Session, SessionIdType, SessionLevel
from nonebot_plugin_session.const import SupportedPlatform

from ..handler import register_receipt_extractor, register_withdraw_function
from ..receipt import Receipt, add_receipt

with suppress(ImportError):
    from nonebot.adapters.dodo import Bot, MessageEvent
    from nonebot.adapters.dodo.models import MessageReturn

    class DodoReceipt(Receipt):
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
        if e or not result or not isinstance(result, MessageReturn):
            return

        island_source_id = None
        channel_id = None
        if api == "set_channel_message_send":
            level = SessionLevel.LEVEL3
            channel_id = data["channel_id"]
            dodo_source_id = data.get("dodo_source_id")
        elif api == "set_personal_message_send":
            level = SessionLevel.LEVEL1
            island_source_id = data["island_source_id"]
            dodo_source_id = data["dodo_source_id"]
        else:
            return

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=SupportedPlatform.dodo,
            level=level,
            id1=dodo_source_id,
            id2=channel_id,
            id3=island_source_id,
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = DodoReceipt(message_id=result.message_id)
        add_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: DodoReceipt):
        await bot.set_channel_message_withdraw(message_id=receipt.message_id)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply:
            return DodoReceipt(message_id=reply.message_id)

from contextlib import suppress
from typing import Any, Optional, cast

from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_session import EventSession, Session, SessionIdType, SessionLevel

from ..handler import register_withdraw_function, withdraw_notice
from ..receipt import Receipt, add_receipt, remove_receipt

with suppress(ImportError):
    from nonebot.adapters.satori import Bot
    from nonebot.adapters.satori.event import MessageDeletedEvent
    from nonebot.adapters.satori.models import MessageObject

    class SatoriReceipt(Receipt):
        channel_id: str
        message_id: str

        def get_id(self) -> str:
            return f"{self.channel_id}_{self.message_id}"

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
        if e or not result or not isinstance(result, list):
            return
        if api not in ["message_create"]:
            return
        if not all(isinstance(msg, MessageObject) for msg in result):
            return
        msg = cast(MessageObject, result[0])
        if not msg.channel:
            return

        level = SessionLevel.LEVEL0
        if msg.guild:
            level = SessionLevel.LEVEL3
        elif msg.member:
            level = SessionLevel.LEVEL2
        elif msg.user:
            level = SessionLevel.LEVEL1
        id1 = data["channel_id"] if level == SessionLevel.LEVEL1 else None
        id2 = msg.channel.id
        id3 = msg.guild.id if msg.guild else None

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=bot.platform,
            level=level,
            id1=id1,
            id2=id2,
            id3=id3,
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = SatoriReceipt(channel_id=msg.channel.id, message_id=msg.id)
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(event: MessageDeletedEvent, session: EventSession):
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = SatoriReceipt(
            channel_id=event.channel.id, message_id=event.message.id
        )
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: SatoriReceipt):
        await bot.message_delete(
            channel_id=receipt.channel_id, message_id=receipt.message_id
        )

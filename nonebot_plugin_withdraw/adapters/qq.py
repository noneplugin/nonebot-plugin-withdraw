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
    from nonebot.adapters.qq import Bot, MessageDeleteEvent, QQMessageEvent
    from nonebot.adapters.qq.models import Message as GuildMessage
    from nonebot.adapters.qq.models import (
        PostC2CMessagesReturn,
        PostGroupMessagesReturn,
    )

    class QQReceipt(Receipt):
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
        if e or not result:
            return

        id1 = None
        id2 = None
        id3 = None
        level = SessionLevel.LEVEL0
        platform = SupportedPlatform.qqguild

        if api == "post_messages":
            if not isinstance(result, GuildMessage):
                return
            level = SessionLevel.LEVEL3
            id3 = result.guild_id
            id2 = result.channel_id
            channel_id = result.channel_id

        elif api == "post_dms_messages":
            if not isinstance(result, GuildMessage):
                return
            level = SessionLevel.LEVEL1
            id3 = data["guild_id"]
            channel_id = result.channel_id

        elif api == "post_c2c_messages":
            if not isinstance(result, PostC2CMessagesReturn):
                return
            level = SessionLevel.LEVEL1
            id1 = data["openid"]
            platform = SupportedPlatform.qq
            channel_id = id1

        elif api == "post_group_messages":
            if not isinstance(result, PostGroupMessagesReturn):
                return
            level = SessionLevel.LEVEL2
            id2 = data["group_openid"]
            platform = SupportedPlatform.qq
            channel_id = id2

        else:
            return

        if not result.id:
            return

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=platform,
            level=level,
            id1=id1,
            id2=id2,
            id3=id3,
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = QQReceipt(channel_id=channel_id, message_id=result.id)
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(event: MessageDeleteEvent, session: EventSession):
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = QQReceipt(
            channel_id=event.message.channel_id, message_id=event.message.id
        )
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: QQReceipt):
        await bot.delete_message(
            channel_id=receipt.channel_id, message_id=receipt.message_id
        )

    @register_receipt_extractor(QQMessageEvent)
    async def _(bot: Bot, event: QQMessageEvent):
        if (reply := getattr(event, "reply", None)) and isinstance(reply, GuildMessage):
            return QQReceipt(channel_id=reply.channel_id, message_id=reply.id)

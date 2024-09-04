from contextlib import suppress
from typing import Any, Optional, Union

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
    from nonebot.adapters.discord import (
        Bot,
        MessageDeleteBulkEvent,
        MessageDeleteEvent,
        MessageEvent,
    )
    from nonebot.adapters.discord.api import UNSET, Channel, ChannelType, MessageGet

    class DiscordReceipt(Receipt):
        channel_id: int
        message_id: int

        def get_id(self) -> str:
            return f"{self.channel_id}_{self.message_id}"

    _channel_cache: dict[int, Channel] = {}

    async def get_channel(bot: Bot, channel_id: int) -> Channel:
        if channel_id in _channel_cache:
            return _channel_cache[channel_id]
        channel = await bot.get_channel(channel_id=channel_id)
        _channel_cache[channel_id] = channel
        return channel

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
        if api not in ["create_message"]:
            return
        if not isinstance(result, MessageGet):
            return

        channel = await get_channel(bot, result.channel_id)

        level = SessionLevel.LEVEL0
        id1 = None
        id2 = str(result.channel_id)
        id3 = None
        if channel.type in [ChannelType.DM]:
            level = SessionLevel.LEVEL1
            id1 = (
                str(channel.recipients[0].id)
                if channel.recipients != UNSET and channel.recipients
                else None
            )
        else:
            level = SessionLevel.LEVEL3
            id3 = str(channel.guild_id) if channel.guild_id != UNSET else None

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=SupportedPlatform.discord,
            level=level,
            id1=id1,
            id2=id2,
            id3=id3,
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = DiscordReceipt(channel_id=result.channel_id, message_id=result.id)
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(
        event: Union[MessageDeleteBulkEvent, MessageDeleteEvent],
        session: EventSession,
    ):
        user_id = session.get_id(SessionIdType.GROUP)
        if isinstance(event, MessageDeleteEvent):
            receipt = DiscordReceipt(channel_id=event.channel_id, message_id=event.id)
            remove_receipt(user_id, receipt)
        else:
            for msg_id in event.ids:
                receipt = DiscordReceipt(channel_id=event.channel_id, message_id=msg_id)
                remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: DiscordReceipt):
        await bot.delete_message(
            channel_id=receipt.channel_id, message_id=receipt.message_id
        )

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply:
            return DiscordReceipt(channel_id=reply.channel_id, message_id=reply.id)

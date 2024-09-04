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
    from nonebot.adapters.kaiheila import Bot
    from nonebot.adapters.kaiheila.api.model import MessageCreateReturn, Quote
    from nonebot.adapters.kaiheila.event import (
        ChannelDeleteMessageEvent,
        MessageEvent,
        PrivateDeleteMessageEvent,
        PrivateMessageEvent,
    )

    class KaiheilaReceipt(Receipt):
        msg_id: str

        def get_id(self) -> str:
            return self.msg_id

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
        if not (
            isinstance(result, MessageCreateReturn)
            and result.msg_id
            and result.msg_timestamp
        ):
            return

        if api == "message_create":
            level = SessionLevel.LEVEL3
            channel_id = data["target_id"]
            user_id = data.get("temp_target_id")
        elif api == "directMessage_create":
            level = SessionLevel.LEVEL1
            channel_id = None
            user_id = data["target_id"]
        else:
            return

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=SupportedPlatform.kaiheila,
            level=level,
            id1=user_id,
            id2=None,
            id3=channel_id,
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = KaiheilaReceipt(msg_id=result.msg_id)
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(
        event: Union[ChannelDeleteMessageEvent, PrivateDeleteMessageEvent],
        session: EventSession,
    ):
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = KaiheilaReceipt(msg_id=event.msg_id)
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: KaiheilaReceipt):
        await bot.message_delete(msg_id=receipt.msg_id)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if isinstance(event, PrivateMessageEvent) and (chat_code := event.event.code):
            message = await bot.directMessage_view(
                chat_code=chat_code, msg_id=event.msg_id
            )
        else:
            message = await bot.message_view(msg_id=event.msg_id)

        quote = message.quote
        if isinstance(quote, Quote) and (msg_id := quote.id_):
            return KaiheilaReceipt(msg_id=msg_id)

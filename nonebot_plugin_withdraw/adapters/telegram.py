from contextlib import suppress
from typing import Any, Optional, Union

from nonebot.adapters import Bot as BaseBot
from nonebot.compat import type_validate_python
from nonebot_plugin_session import Session, SessionIdType, SessionLevel
from nonebot_plugin_session.const import SupportedPlatform

from ..handler import register_receipt_extractor, register_withdraw_function
from ..receipt import Receipt, add_receipt

with suppress(ImportError):
    from nonebot.adapters.telegram import Bot
    from nonebot.adapters.telegram.event import MessageEvent
    from nonebot.adapters.telegram.model import Message as TGMessage

    class TelegramReceipt(Receipt):
        chat_id: Union[int, str]
        message_id: int

        def get_id(self) -> str:
            return f"{self.chat_id}_{self.message_id}"

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

        if api in [
            "send_message",
            "send_photo",
            "send_audio",
            "send_document",
            "send_video",
            "send_animation",
            "send_voice",
            "send_video_note",
            "send_location",
            "send_venue",
            "send_contact",
            "send_poll",
            "send_dice",
            "send_sticker",
            "send_invoice",
        ]:
            msg = type_validate_python(TGMessage, result)

        elif api == "send_media_group":
            msg = type_validate_python(TGMessage, result[0])

        else:
            return

        message_thread_id = msg.message_thread_id
        chat_id = msg.chat.id
        id1 = None
        id2 = None
        id3 = None
        if message_thread_id:
            id3 = str(chat_id)
            id2 = str(message_thread_id)
            level = SessionLevel.LEVEL3
        elif msg.chat.type == "private":
            id1 = str(chat_id)
            level = SessionLevel.LEVEL1
        else:
            id2 = str(chat_id)
            level = SessionLevel.LEVEL2

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=SupportedPlatform.telegram,
            level=level,
            id1=id1,
            id2=id2,
            id3=id3,
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = TelegramReceipt(chat_id=msg.chat.id, message_id=msg.message_id)
        add_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: TelegramReceipt):
        await bot.delete_message(chat_id=receipt.chat_id, message_id=receipt.message_id)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply_to_message:
            return TelegramReceipt(chat_id=reply.chat.id, message_id=reply.message_id)

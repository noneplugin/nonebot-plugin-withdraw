from contextlib import suppress
from typing import Any, Optional, Union

from nonebot.adapters import Bot as BaseBot
from nonebot.compat import type_validate_python
from nonebot_plugin_uninfo import (
    Scene,
    SceneType,
    Session,
    SupportAdapter,
    SupportScope,
    User,
)

from ..handler import register_receipt_extractor, register_withdraw_function
from ..receipt import Receipt, add_receipt
from ..utils import get_user_id

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
        parent = None
        if message_thread_id:
            scene_type = SceneType.CHANNEL_TEXT
            scene_id = str(message_thread_id)
            parent = Scene(id=str(chat_id), type=SceneType.GUILD)
        elif msg.chat.type == "private":
            scene_type = SceneType.PRIVATE
            scene_id = str(chat_id)
        else:
            scene_type = SceneType.GROUP
            scene_id = str(chat_id)

        session = Session(
            self_id=bot.self_id,
            adapter=SupportAdapter.telegram,
            scope=SupportScope.telegram,
            scene=Scene(id=scene_id, type=scene_type, parent=parent),
            user=User(id=bot.self_id),
        )
        user_id = get_user_id(session)
        receipt = TelegramReceipt(chat_id=msg.chat.id, message_id=msg.message_id)
        add_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: TelegramReceipt):
        await bot.delete_message(chat_id=receipt.chat_id, message_id=receipt.message_id)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply_to_message:
            return TelegramReceipt(chat_id=reply.chat.id, message_id=reply.message_id)

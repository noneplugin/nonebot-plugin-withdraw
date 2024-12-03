from contextlib import suppress
from typing import Any, Optional

from nonebot.adapters import Bot as BaseBot
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

        if api == "set_channel_message_send":
            scene_type = SceneType.CHANNEL_TEXT
            scene_id = data["channel_id"]
            parent = None
        elif api == "set_personal_message_send":
            scene_type = SceneType.PRIVATE
            scene_id = data["dodo_source_id"]
            parent = Scene(id=data["island_source_id"], type=SceneType.GUILD)
        else:
            return

        session = Session(
            self_id=bot.self_id,
            adapter=SupportAdapter.dodo,
            scope=SupportScope.dodo,
            scene=Scene(id=scene_id, type=scene_type, parent=parent),
            user=User(id=bot.self_id),
        )
        user_id = get_user_id(session)
        receipt = DodoReceipt(message_id=result.message_id)
        add_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: DodoReceipt):
        await bot.set_channel_message_withdraw(message_id=receipt.message_id)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply:
            return DodoReceipt(message_id=reply.message_id)

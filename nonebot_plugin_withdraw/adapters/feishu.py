import re
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
    from nonebot.adapters.feishu import Bot, MessageEvent

    class FeishuReceipt(Receipt):
        message_id: str

        def get_id(self) -> str:
            return self.message_id

    _chat_info_cache: dict[str, dict[str, Any]] = {}

    async def get_chat_info(bot: Bot, chat_id: str) -> dict[str, Any]:
        if chat_id in _chat_info_cache:
            return _chat_info_cache[chat_id]
        params = {"method": "GET", "query": {"user_id_type": "open_id"}}
        resp = await bot.call_api(f"im/v1/chats/{chat_id}", **params)
        _chat_info_cache[chat_id] = resp
        return resp

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
        if not (api == "im/v1/messages" or re.match(r"im/v1/messages/\S+/reply", api)):
            return

        result_data = result["data"]
        chat_id = result_data["chat_id"]
        resp = await get_chat_info(bot, chat_id)
        chat_mode = resp["data"]["chat_mode"]

        if chat_mode == "p2p":
            scene_type = SceneType.PRIVATE
        elif chat_mode == "group":
            scene_type = SceneType.GROUP

        session = Session(
            self_id=bot.self_id,
            adapter=SupportAdapter.feishu,
            scope=SupportScope.feishu,
            scene=Scene(id=chat_id, type=scene_type),
            user=User(id=bot.self_id),
        )
        user_id = get_user_id(session)
        receipt = FeishuReceipt(message_id=result_data["message_id"])
        add_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: FeishuReceipt):
        params = {"method": "DELETE"}
        return await bot.call_api(f"im/v1/messages/{receipt.message_id}", **params)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply:
            return FeishuReceipt(message_id=reply.message_id)

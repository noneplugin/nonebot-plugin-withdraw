from contextlib import suppress
from typing import Any, Optional

from nonebot.adapters import Bot as BaseBot
from nonebot.compat import type_validate_python
from nonebot_plugin_session import Session, SessionIdType, SessionLevel
from nonebot_plugin_session.const import SupportedPlatform

from ..handler import register_withdraw_function
from ..receipt import Receipt, add_receipt

with suppress(ImportError):
    from nonebot.adapters.red import Bot
    from nonebot.adapters.red.api.model import ChatType
    from nonebot.adapters.red.api.model import Message as MessageModel

    class RedReceipt(Receipt):
        chatType: ChatType
        peerUin: str
        msgId: str

        def get_id(self) -> str:
            return f"{self.chatType}_{self.peerUin}_{self.msgId}"

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
        if api not in ["send_message"]:
            return

        resp = type_validate_python(MessageModel, result)
        peerUin = resp.peerUin or resp.peerUid
        if not peerUin:
            return

        id1 = None
        id2 = None
        level = SessionLevel.LEVEL0
        if resp.chatType == ChatType.GROUP:
            id2 = peerUin
            level = SessionLevel.LEVEL2
        elif resp.chatType == ChatType.FRIEND:
            id1 = peerUin
            level = SessionLevel.LEVEL1

        session = Session(
            bot_id=bot.self_id,
            bot_type=bot.type,
            platform=SupportedPlatform.qq,
            level=level,
            id1=id1,
            id2=id2,
        )
        user_id = session.get_id(SessionIdType.GROUP)
        receipt = RedReceipt(chatType=resp.chatType, peerUin=peerUin, msgId=resp.msgId)
        add_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: RedReceipt):
        await bot.recall_message(receipt.chatType, receipt.peerUin, receipt.msgId)

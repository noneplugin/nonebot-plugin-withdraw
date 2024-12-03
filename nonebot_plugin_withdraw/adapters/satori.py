from contextlib import suppress
from typing import Any, Optional, cast

from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_uninfo import (
    Scene,
    SceneType,
    Session,
    SupportAdapter,
    SupportScope,
    User,
)

from ..handler import register_withdraw_function, withdraw_notice
from ..receipt import Receipt, add_receipt, remove_receipt
from ..utils import UserId, get_user_id

with suppress(ImportError):
    from nonebot.adapters.satori import Bot
    from nonebot.adapters.satori.event import MessageDeletedEvent
    from nonebot.adapters.satori.models import MessageObject
    from nonebot_plugin_uninfo.adapters.satori.main import TYPE_MAPPING

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
        for res in result:
            if not isinstance(res, MessageObject):
                return
        result_messages = cast(list[MessageObject], result)
        msg = result_messages[0]

        parent = None

        if msg.guild and msg.channel:
            scene_type = TYPE_MAPPING[msg.channel.type]
            scene_id = msg.channel.id
            parent = Scene(id=msg.guild.id, type=SceneType.GUILD)
            if (
                "guild.plain" in bot._self_info.features
                or msg.guild.id == msg.channel.id
            ):
                scene_type = SceneType.GROUP
                parent.type = SceneType.GROUP

        elif msg.guild:
            scene_type = (
                SceneType.GROUP
                if "guild.plain" in bot._self_info.features
                else SceneType.GUILD
            )
            scene_id = msg.guild.id

        elif msg.channel:
            scene_type = (
                SceneType.GROUP
                if "guild.plain" in bot._self_info.features
                else SceneType.GUILD
            )
            scene_id = msg.channel.id

        else:
            return

        session = Session(
            self_id=bot.self_id,
            adapter=SupportAdapter.satori,
            scope=SupportScope.ensure_satori(bot.platform),
            scene=Scene(id=scene_id, type=scene_type, parent=parent),
            user=User(id=bot.self_id),
        )
        user_id = get_user_id(session)
        assert msg.channel
        receipt = SatoriReceipt(channel_id=msg.channel.id, message_id=msg.id)
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(event: MessageDeletedEvent, user_id: UserId):
        receipt = SatoriReceipt(
            channel_id=event.channel.id, message_id=event.message.id
        )
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: SatoriReceipt):
        await bot.message_delete(
            channel_id=receipt.channel_id, message_id=receipt.message_id
        )

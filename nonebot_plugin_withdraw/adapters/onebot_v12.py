from contextlib import suppress
from typing import Any, Optional, Union

from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_uninfo import (
    Scene,
    SceneType,
    Session,
    SupportAdapter,
    SupportScope,
    User,
)

from ..handler import (
    register_receipt_extractor,
    register_withdraw_function,
    withdraw_notice,
)
from ..receipt import Receipt, add_receipt, remove_receipt
from ..utils import UserId, get_user_id

with suppress(ImportError):
    from nonebot.adapters.onebot.v12 import (
        Bot,
        GroupMessageDeleteEvent,
        MessageEvent,
        PrivateMessageDeleteEvent,
    )

    class OnebotV12Receipt(Receipt):
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
        if e or not result:
            return

        if api not in ["send_message"]:
            return

        parent = None
        detail_type = data["detail_type"]
        if detail_type == "channel":
            scene_type = SceneType.CHANNEL_TEXT
            scene_id = data["channel_id"]
            parent = (
                Scene(id=data["guild_id"], type=SceneType.GUILD)
                if data.get("guild_id")
                else None
            )
        elif detail_type == "group":
            scene_type = SceneType.GROUP
            scene_id = data["group_id"]
        elif detail_type == "private":
            scene_type = SceneType.PRIVATE
            scene_id = data["user_id"]
        else:
            return

        session = Session(
            self_id=bot.self_id,
            adapter=SupportAdapter.onebot12,
            scope=SupportScope.ensure_ob12(bot.platform),
            scene=Scene(id=scene_id, type=scene_type, parent=parent),
            user=User(id=bot.self_id),
        )
        user_id = get_user_id(session)
        receipt = OnebotV12Receipt(message_id=result["message_id"])
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(
        event: Union[GroupMessageDeleteEvent, PrivateMessageDeleteEvent],
        user_id: UserId,
    ):
        receipt = OnebotV12Receipt(message_id=event.message_id)
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: OnebotV12Receipt):
        await bot.delete_message(message_id=receipt.message_id)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply:
            return OnebotV12Receipt(message_id=reply.message_id)

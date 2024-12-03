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
    from nonebot.adapters.onebot.v11 import (
        Bot,
        FriendRecallNoticeEvent,
        GroupRecallNoticeEvent,
        MessageEvent,
    )

    class OnebotV11Receipt(Receipt):
        message_id: int

        def get_id(self) -> str:
            return str(self.message_id)

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
        if api not in ["send_msg", "send_private_msg", "send_group_msg"]:
            return

        if api == "send_group_msg" or (
            api == "send_msg"
            and (
                data.get("message_type") == "group"
                or (data.get("message_type") is None and data.get("group_id"))
            )
        ):
            scene_id = str(data["group_id"])
            scene_type = SceneType.GROUP
        else:
            scene_id = str(data["user_id"])
            scene_type = SceneType.PRIVATE

        session = Session(
            self_id=bot.self_id,
            adapter=SupportAdapter.onebot11,
            scope=SupportScope.qq_client,
            scene=Scene(id=scene_id, type=scene_type),
            user=User(id=bot.self_id),
        )
        user_id = get_user_id(session)
        receipt = OnebotV11Receipt(message_id=result["message_id"])
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(
        event: Union[GroupRecallNoticeEvent, FriendRecallNoticeEvent],
        user_id: UserId,
    ):
        receipt = OnebotV11Receipt(message_id=event.message_id)
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: OnebotV11Receipt):
        await bot.delete_msg(message_id=receipt.message_id)

    @register_receipt_extractor(MessageEvent)
    async def _(bot: Bot, event: MessageEvent):
        if reply := event.reply:
            return OnebotV11Receipt(message_id=reply.message_id)

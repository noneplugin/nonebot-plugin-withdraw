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

from ..handler import (
    register_receipt_extractor,
    register_withdraw_function,
    withdraw_notice,
)
from ..receipt import Receipt, add_receipt, remove_receipt
from ..utils import UserId, get_user_id

with suppress(ImportError):
    from nonebot.adapters.qq import Bot, MessageDeleteEvent, QQMessageEvent
    from nonebot.adapters.qq.models import Message as GuildMessage
    from nonebot.adapters.qq.models import (
        PostC2CMessagesReturn,
        PostGroupMessagesReturn,
    )

    class QQReceipt(Receipt):
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
        if e or not result:
            return
        if api not in (
            "post_messages",
            "post_dms_messages",
            "post_c2c_messages",
            "post_group_messages",
        ):
            return

        parent = None

        if api == "post_messages":
            assert isinstance(result, GuildMessage)
            scene_type = SceneType.CHANNEL_TEXT
            scene_id = result.channel_id
            parent = Scene(id=result.guild_id, type=SceneType.GUILD)

        elif api == "post_dms_messages":
            assert isinstance(result, GuildMessage)
            scene_type = SceneType.PRIVATE
            scene_id = result.channel_id
            parent = Scene(id=result.guild_id, type=SceneType.GUILD)

        elif api == "post_c2c_messages":
            assert isinstance(result, PostC2CMessagesReturn)
            scene_type = SceneType.PRIVATE
            scene_id = data["openid"]

        elif api == "post_group_messages":
            assert isinstance(result, PostGroupMessagesReturn)
            scene_type = SceneType.GROUP
            scene_id = data["group_openid"]

        session = Session(
            self_id=bot.self_id,
            adapter=SupportAdapter.qq,
            scope=SupportScope.qq_api,
            scene=Scene(id=scene_id, type=scene_type, parent=parent),
            user=User(id=bot.self_id),
        )

        assert result.id
        user_id = get_user_id(session)
        receipt = QQReceipt(channel_id=scene_id, message_id=result.id)
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(event: MessageDeleteEvent, user_id: UserId):
        receipt = QQReceipt(
            channel_id=event.message.channel_id, message_id=event.message.id
        )
        remove_receipt(user_id, receipt)

    @register_withdraw_function(Bot)
    async def _(bot: Bot, receipt: QQReceipt):
        await bot.delete_message(
            channel_id=receipt.channel_id, message_id=receipt.message_id
        )

    @register_receipt_extractor(QQMessageEvent)
    async def _(bot: Bot, event: QQMessageEvent):
        if (reply := getattr(event, "reply", None)) and isinstance(reply, GuildMessage):
            return QQReceipt(channel_id=reply.channel_id, message_id=reply.id)

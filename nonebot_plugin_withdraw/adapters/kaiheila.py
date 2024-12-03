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

        scene_id = data["target_id"]
        if api == "message_create":
            scene_type = SceneType.CHANNEL_TEXT
        elif api == "directMessage_create":
            scene_type = SceneType.PRIVATE
        else:
            return

        session = Session(
            self_id=bot.self_id,
            adapter=SupportAdapter.kook,
            scope=SupportScope.kook,
            scene=Scene(id=scene_id, type=scene_type),
            user=User(id=bot.self_id),
        )
        user_id = get_user_id(session)
        receipt = KaiheilaReceipt(msg_id=result.msg_id)
        add_receipt(user_id, receipt)

    @withdraw_notice.handle()
    def _(
        event: Union[ChannelDeleteMessageEvent, PrivateDeleteMessageEvent],
        user_id: UserId,
    ):
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

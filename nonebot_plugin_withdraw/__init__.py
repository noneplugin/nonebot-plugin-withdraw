import traceback

from nonebot import require
from nonebot.adapters import Bot, Event
from nonebot.exception import AdapterException
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me

require("nonebot_plugin_alconna")
require("nonebot_plugin_session")

from nonebot_plugin_alconna import Alconna, Args, on_alconna
from nonebot_plugin_session import SessionIdType, extract_session

from . import adapters as adapters
from .config import Config
from .handler import extract_receipt, withdraw_message
from .receipt import pop_receipt, remove_receipt

__plugin_meta__ = PluginMetadata(
    name="撤回",
    description="自助撤回机器人发出的消息",
    usage=(
        "1、@我 撤回 [num]，num 指机器人发的倒数第几条消息，从 0 开始，默认为 0\n"
        "2、回复需要撤回的消息，回复“撤回”"
    ),
    type="application",
    homepage="https://github.com/noneplugin/nonebot-plugin-withdraw",
    config=Config,
    supported_adapters={
        "~onebot.v11",
        "~onebot.v12",
        "~kaiheila",
        "~telegram",
        "~feishu",
        "~red",
        "~discord",
        "~qq",
        "~dodo",
        "~satori",
    },
)


withdraw = on_alconna(
    Alconna("撤回", Args["num", int, 0]),
    block=True,
    rule=to_me(),
    use_cmd_start=True,
)


@withdraw.handle()
async def _(matcher: Matcher, bot: Bot, event: Event, num: int):
    user_id = extract_session(bot, event).get_id(SessionIdType.GROUP)

    receipt = await extract_receipt(bot, event)
    if not receipt:
        receipt = pop_receipt(user_id, num)
    if not receipt:
        await matcher.finish("找不到要撤回的消息")

    try:
        await withdraw_message(bot, receipt)
    except AdapterException:
        logger.warning(traceback.format_exc())
        await matcher.finish("撤回失败")
    finally:
        remove_receipt(user_id, receipt)

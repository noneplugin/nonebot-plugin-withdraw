from typing import Any, Dict, List, Tuple, Optional
from nonebot import get_driver, on_command, on_notice
from nonebot.internal.adapter import Bot as BaseBot
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
    GroupRecallNoticeEvent,
)
from nonebot.params import Command, CommandArg, RawCommand

from .config import Config

withdraw_config = Config.parse_obj(get_driver().config.dict())


__help__plugin_name__ = "withdraw"
__des__ = "自助撤回机器人发出的消息"
__cmd__ = """
1、@我 撤回 [num]，num 为机器人发的倒数第几条消息，从 0 开始，默认为 0
2、回复需要撤回的消息，回复“撤回”
""".strip()
__short_cmd__ = "@我 撤回、回复消息“撤回”"
__usage__ = f"{__des__}\nUsage:\n{__cmd__}"


msg_ids: Dict[str, List[int]] = {}
max_size = withdraw_config.withdraw_max_size


def get_key(msg_type: str, id: int):
    return f"{msg_type}_{id}"


async def save_msg_id(
    bot: BaseBot, e: Optional[Exception], api: str, data: Dict[str, Any], result: Any
):
    try:
        if api == "send_msg":
            msg_type = data["message_type"]
            id = data["group_id"] if msg_type == "group" else data["user_id"]
        elif api == "send_private_msg":
            msg_type = "private"
            id = data["user_id"]
        elif api == "send_group_msg":
            msg_type = "group"
            id = data["group_id"]
        else:
            return
        key = get_key(msg_type, id)
        msg_id = int(result["message_id"])

        if key not in msg_ids:
            msg_ids[key] = []
        msg_ids[key].append(msg_id)
        if len(msg_ids) > max_size:
            msg_ids[key].pop(0)
    except:
        pass


Bot.on_called_api(save_msg_id)


# 命令前缀为空则需要to_me，否则不需要
def smart_to_me(
    event: MessageEvent, cmd: Tuple[str, ...] = Command(), raw_cmd: str = RawCommand()
) -> bool:
    return not raw_cmd.startswith(cmd[0]) or event.is_tome()


withdraw = on_command("withdraw", aliases={"撤回"}, block=True, rule=smart_to_me)


@withdraw.handle()
async def _(bot: Bot, event: MessageEvent, msg: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent):
        msg_type = "group"
        id = event.group_id
    else:
        msg_type = "private"
        id = event.user_id
    key = get_key(msg_type, id)

    if event.reply:
        msg_id = event.reply.message_id
        try:
            await bot.delete_msg(message_id=msg_id)
            return
        except:
            await withdraw.finish("撤回失败，可能已超时")

    num = msg.extract_plain_text().strip()
    if num and num.isdigit() and 0 <= int(num) < len(msg_ids[key]):
        num = int(num)
    else:
        num = 0

    try:
        idx = -num - 1
        await bot.delete_msg(message_id=msg_ids[key][idx])
        msg_ids[key].pop(idx)
    except:
        await withdraw.finish("撤回失败，可能已超时")


async def _group_recall(bot: Bot, event: GroupRecallNoticeEvent) -> bool:
    return str(event.user_id) == str(bot.self_id)


withdraw_notice = on_notice(_group_recall)


@withdraw_notice.handle()
async def _(event: GroupRecallNoticeEvent):
    msg_id = event.message_id
    id = event.group_id
    key = get_key("group", id)
    if key in msg_ids and msg_id in msg_ids[key]:
        msg_ids[key].remove(msg_id)

import functools
from nonebot import get_driver, on_command
from nonebot.adapters.cqhttp import Bot, Event, GroupMessageEvent
from nonebot.rule import to_me
from nonebot.typing import T_State

from .config import Config
global_config = get_driver().config
withdraw_config = Config(**global_config.dict())

msg_ids = {}
max_size = withdraw_config.withdraw_max_size


def save_msg_id(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)

        try:
            event = kwargs['event']
            if isinstance(event, GroupMessageEvent):
                id = event.group_id
                msg_id = result['message_id']

                if id not in msg_ids:
                    msg_ids[id] = []
                msg_ids[id].append(msg_id)
                if len(msg_ids) > max_size:
                    msg_ids[id].pop(0)
        except:
            pass

        return result
    return wrapper


Bot.send = save_msg_id(Bot.send)

withdraw = on_command('withdraw', aliases={'delete', '撤回'}, rule=to_me())


@withdraw.handle()
async def _(bot: Bot, event: Event, state: T_State):
    if not isinstance(event, GroupMessageEvent):
        return
    id = event.group_id

    async def delete_msg(num):
        try:
            await bot.delete_msg(message_id=msg_ids[id].pop(-num - 1))
            return True
        except:
            return False

    num = event.get_plaintext().strip()
    if not num:
        num = 0
    elif num.isdigit() and 0 <= int(num) < len(msg_ids[id]):
        num = int(num)
    else:
        return

    if not await delete_msg(num):
        await withdraw.finish('撤回失败，可能已超时')

from typing import Annotated

from nonebot.params import Depends
from nonebot_plugin_uninfo import Uninfo


def get_user_id(uninfo: Uninfo) -> str:
    return f"{uninfo.scope}_{uninfo.self_id}_{uninfo.scene_path}"


UserId = Annotated[str, Depends(get_user_id)]

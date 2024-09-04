from nonebot.plugin import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    withdraw_max_size: int = 20


withdraw_config = get_plugin_config(Config)

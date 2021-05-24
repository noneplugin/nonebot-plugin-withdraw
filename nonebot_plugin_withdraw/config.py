from pydantic import BaseSettings


class Config(BaseSettings):
    withdraw_max_size: int = 10

    class Config:
        extra = 'ignore'

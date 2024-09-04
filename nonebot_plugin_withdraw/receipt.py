from typing import Optional

from pydantic import BaseModel

from .config import withdraw_config


class Receipt(BaseModel):
    def get_id(self) -> str:
        raise NotImplementedError

    def __eq__(self, other: "Receipt") -> bool:
        return self.get_id() == other.get_id()

    def __hash__(self) -> int:
        return hash(self.get_id())


_receipt_records: dict[str, list[Receipt]] = {}


def add_receipt(user_id: str, receipt: Receipt):
    if user_id not in _receipt_records:
        _receipt_records[user_id] = []
    if receipt not in _receipt_records[user_id]:
        _receipt_records[user_id].append(receipt)
    if len(_receipt_records[user_id]) > withdraw_config.withdraw_max_size:
        _receipt_records[user_id].pop(0)


def remove_receipt(user_id: str, receipt: Receipt):
    if user_id in _receipt_records and receipt in _receipt_records[user_id]:
        _receipt_records[user_id].remove(receipt)


def pop_receipt(user_id: str) -> Optional[Receipt]:
    if user_id in _receipt_records and _receipt_records[user_id]:
        return _receipt_records[user_id].pop()
    return None

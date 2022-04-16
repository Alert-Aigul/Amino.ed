from hashlib import sha1
import hmac
import json
import os

from time import time
from typing import Any, Dict, List, Union
from ujson import loads
from base64 import b64decode, b64encode
from functools import cache, reduce

PREFIX = bytes.fromhex("42")
SIG_KEY = bytes.fromhex("F8E7A61AC3F725941E3AC7CAE2D688BE97F30B93")
DEVICE_KEY = bytes.fromhex("02B258C63559D8804321C5D5065AF320358D366F")


@cache
def generate_device(data: bytes = None) -> str:
    identifier = b"ED==" + data or os.urandom(16)
    mac = hmac.new(DEVICE_KEY, PREFIX + identifier, sha1)
    return f"{PREFIX.hex()}{identifier.hex()}{mac.hexdigest()}".upper()


def generate_signature(data: Union[str, bytes]) -> str:
    data = data if isinstance(data, bytes) else data.encode("utf-8")
    return b64encode(PREFIX + hmac.new(SIG_KEY, data, sha1).digest()).decode("utf-8")


def get_timers(size: int) -> List[Dict[str, int]]:
    return tuple(map(lambda _: {"start": int(time()), "end": int(time() + 300)}, range(size)))


def decode_sid(sid: str) -> dict:
    args = (lambda a, e: a.replace(*e), ("-+", "_/"), sid+"="*(-len(sid) % 4))
    return loads(b64decode(reduce(*args).encode())[1:-20].decode())


def sid_to_uid(sid: str) -> str:
    return decode_sid(sid)["2"]


def sid_to_ip_address(sid: str) -> str:
    return decode_sid(sid)["4"]


def is_json(myjson) -> bool:
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

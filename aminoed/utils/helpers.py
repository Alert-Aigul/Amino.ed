import json
import aiohttp
import requests

from time import time
from typing import Any, Dict, List
from ujson import loads
from base64 import b64decode
from functools import reduce

sync_session = requests.Session()
session = aiohttp.ClientSession()


def generate_device_sync() -> str:
    return sync_session.get("https://ed-generators.herokuapp.com/device").text
    

async def generate_device(data: str = None) -> str:
    return await (await session.get("https://ed-generators.herokuapp.com/device" + f"?data={data}" if data else "")).text()
    

async def generate_signature(data: Any) -> str:
    return await (await session.post("https://ed-generators.herokuapp.com/signature", data=data)).text()


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

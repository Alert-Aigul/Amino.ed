from time import time
from ujson import loads
from base64 import b64decode
from functools import reduce

from aminoed.generators import GeneratorSocket

signature_generator = GeneratorSocket()
DEVICE_ID = "42A228D23F75172D80BE59844A973B1835929C99014D4CA661366BFE4C3FE915EC3DFEFF4587FB9DB4"


async def generate_device() -> str:
    return DEVICE_ID
    

async def generate_signature(data: str) -> str:
    return await signature_generator.get(data)


def get_timers(size: int) -> list[dict[str, int]]:
    return tuple(map(lambda _: {"start": int(time()), "end": int(time() + 300)}, range(size)))


def decode_sid(sid: str) -> dict:
    args = (lambda a, e: a.replace(*e), ("-+", "_/"), sid+"="*(-len(sid) % 4))
    return loads(b64decode(reduce(*args).encode())[1:-20].decode())


def sid_to_uid(sid: str) -> str:
    return decode_sid(sid)["2"]


def sid_to_ip_address(sid: str) -> str:
    return decode_sid(sid)["4"]

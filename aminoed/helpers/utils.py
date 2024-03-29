import asyncio
import hmac
import os
import json

from hashlib import sha1
from time import time
from typing import Any, Dict, List, Union
from aiofile import async_open
from base64 import urlsafe_b64decode, b64encode, urlsafe_b64encode

from .models import SID

PREFIX = bytes.fromhex("19")
SIG_KEY = bytes.fromhex("DFA5ED192DDA6E88A12FE12130DC6206B1251E44")
DEVICE_KEY = bytes.fromhex("E7309ECC0953C6FA60005B2765F99DBBC965C8E9")

try:
    with open(".ed.json") as file:
        CACHE = json.loads(file.read())
except ValueError:
    CACHE = {}
except FileNotFoundError:
    CACHE = {}
except FileExistsError:
    CACHE = {}

CACHE_LOCK = asyncio.Lock()


def generate_device(data: bytes = None) -> str:
    identifier = data or os.urandom(20)
    mac = hmac.new(DEVICE_KEY, PREFIX + identifier, sha1)
    return f"{PREFIX.hex()}{identifier.hex()}{mac.hexdigest()}".upper()


def update_device(deviceId: str) -> str:
    return generate_device(bytes.fromhex(deviceId[2:42]))


def generate_signature(data: Union[str, bytes]) -> str:
    data = data if isinstance(data, bytes) else data.encode("utf-8")
    return b64encode(PREFIX + hmac.new(SIG_KEY, data, sha1).digest()).decode("utf-8")


def get_timers(size: int) -> List[Dict[str, int]]:
    return tuple(map(lambda _: {"start": int(time()), "end": int(time() + 300)}, range(size)))


def generate_sid(key: str, userId: str, ip: str, timestamp: int = int(time()), clientType: int = 100) -> str:
    data = {
        "1": None, 
        "0": 2, 
        "3": 0, 
        "2": userId, 
        "5": timestamp, 
        "4": ip, 
        "6": clientType
    }
    
    identifier = b"\x02" + json.dumps(data).encode()
    mac = hmac.new(bytes.fromhex(key), identifier, sha1)
    return urlsafe_b64encode(identifier + mac.digest()).decode().replace("=", "")


def decode_sid(sid: str) -> SID:
    fixed_sid = sid + "=" * (4 - len(sid) % 4)
    uncoded_sid = urlsafe_b64decode(fixed_sid)
    
    prefix = uncoded_sid[:1].hex()
    signature = uncoded_sid[-20:].hex()
    data = json.loads(uncoded_sid[1:-20])
    
    return SID(
        original=sid, 
        prefix=prefix, 
        signature=signature, 
        data=data, **data
    )
    
    
def decode_secret(secret: str) -> SID:
    info = secret.split()
    
    info[0] = int(info[0])
    info[5] = int(info[5])
    info[6] = int(info[6])
    
    return info


def secret_expired(secret: str) -> bool:
    return int(time()) - decode_secret(secret)[6] > 1209600


def sid_expired(sid: str) -> bool:
    return int(time()) - decode_sid(sid).makeTime > 43200
    

def is_json(myjson) -> bool:
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


async def set_cache(key: str, value: Any, is_temp: bool = False) -> Any:
    global CACHE
    
    async with CACHE_LOCK:    
        CACHE.update({key: value})
        
        if is_temp:
            return
        
        async with async_open(".ed.json", "w") as file:
            await file.write(json.dumps(CACHE))


async def get_cache(key: str, default: Any = None) -> Any:
    global CACHE
    
    async with CACHE_LOCK:    
        return CACHE.get(key, default)


def properties(objects: list, name: str):
    return [getattr(o, name) for o in objects]


def list_to_lists(list: list, values_per_list: int):
    return [list[i:i +values_per_list] for i in range(0, len(list), values_per_list)]


def jsonify(**kwargs) -> Dict:
    return kwargs

def get_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()  
    except RuntimeError:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            
    return loop

def get_ndc(ndc_id) -> str:
    if (ndc_id == 0):
        return "/g/s"
    
    elif (ndc_id > 0):
        return f"/x{ndc_id}/s"
    
    return f"/g/s-x{abs(ndc_id)}"

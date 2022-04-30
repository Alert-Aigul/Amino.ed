__title__ = 'Amino.ed'
__author__ = 'Alert Aigul'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020-2022 Alert'
__version__ = '2.6.0'

from asyncio import get_event_loop
from asyncio.events import AbstractEventLoop
from requests import get

from .global_client import Client
from .community_client import CommunityClient
from .utils import exceptions, models, types, helpers
from .websocket import WebSocketClient

from .utils.helpers import *
from .utils.types import *
from .utils.models import *
from .utils.exceptions import *


def run_with_client(event_loop: AbstractEventLoop = None, deviceId: str = None):
    async def start(loop, callback):
        async with Client(loop, deviceId) as client:
            await callback(client)

    def _start(callback):
        loop = event_loop or get_event_loop()
        loop.run_until_complete(start(loop, callback))
    return _start

def run():
    def start(callback):
        loop = get_event_loop()
        loop.run_until_complete(callback())
    return start


__newest__ = get("https://pypi.python.org/pypi/Amino.ed/json").json()["info"]["version"]

if __version__ != __newest__:
    print(f"New version available: {__newest__} (Using {__version__})")

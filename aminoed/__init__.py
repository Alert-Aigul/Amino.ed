__title__ = 'Amino.ed'
__author__ = 'Alert Aigul'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020-2022 Alert'
__version__ = '2.7.3'

from asyncio import sleep, create_task, gather
from asyncio.events import AbstractEventLoop
from requests import get

from .client import Client
from .websocket import AminoWebSocket

from .helpers.utils import *
from .helpers.types import *
from .helpers.models import *
from .helpers.exceptions import *
from .helpers.event import *


def run_with_client(
    ndc_id: str = None, 
    device_id: str = None,
    event_loop: AbstractEventLoop = None
):
    async def start(loop, callback):
        async with Client(ndc_id, device_id, loop) as client:
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

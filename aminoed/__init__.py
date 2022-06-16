__title__ = 'Amino.ed'
__author__ = 'Alert Aigul'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020-2022 Alert'
__version__ = '2.8.0.1'

from asyncio import sleep, create_task, gather
from asyncio.events import AbstractEventLoop

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
    check_updates: bool = True,
    event_loop: AbstractEventLoop = None
):
    async def start(loop, callback):
        async with Client(
            ndc_id, 
            device_id, 
            loop, 
            check_updates=check_updates
        ) as client:
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

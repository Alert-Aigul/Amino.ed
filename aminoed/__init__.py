__title__ = 'Amino.ed'
__author__ = 'Alert Aigul'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020-2022 Alert'
__version__ = '2.8.3.1'

from asyncio import sleep, create_task, gather
from asyncio.events import AbstractEventLoop

from aiohttp import BaseConnector

from .http import HttpClient
from .client import Client
from .websocket import AminoWebSocket

from .helpers.utils import *
from .helpers.types import *
from .helpers.models import *
from .helpers.exceptions import *
from .helpers.event import *

RU: str = Language.RU
ENG: str = Language.ENG

def set_lang(lang: str = Language.ENG):
    HttpClient.LANGUAGE = lang


def run_with_client(
    check_updates: bool = True,
    ndc_id: Optional[str] = None,
    device_id: Optional[str] = None,
    loop: Optional[AbstractEventLoop] = None,
    proxy: Optional[str] = None,
    proxy_auth: Optional[str] = None,
    timeout: Optional[int] = None,
    connector: Optional[BaseConnector] = None,
    session: Optional[ClientSession] = None,
) -> None:
    async def start(loop, callback):
        async with Client(
            ndc_id, 
            device_id, 
            loop, 
            proxy, 
            proxy_auth,
            timeout, 
            None,
            session,
            connector, 
            check_updates
        ) as client:
            await callback(client)

    def _start(callback):
        nonlocal loop
        
        loop = loop or get_event_loop()
        loop.run_until_complete(start(loop, callback))
    return _start


def run():
    def start(callback):
        loop = get_event_loop()
        loop.run_until_complete(callback())
    return start

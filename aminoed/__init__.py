__title__ = 'Amino.ed'
__author__ = 'Alert Aigul'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020-2023 Alert'
__version__ = '2.8.4.13'

from asyncio import sleep, create_task, gather
from asyncio.events import AbstractEventLoop
import signal
from .helpers.utils import *

loop = get_event_loop()

from aiohttp import BaseConnector, ClientSession
ClientSession.__del__ = lambda _: None
BaseConnector.__del__ = lambda _: None

from .http import HttpClient

from .client import Client
from .websocket import AminoWebSocket

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
    loop: Optional[AbstractEventLoop] = loop,
    proxy: Optional[str] = None,
    proxy_auth: Optional[str] = None,
    timeout: Optional[int] = None,
    connector: Optional[BaseConnector] = None,
    session: Optional[ClientSession] = None,
    debug: bool = False
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
            check_updates,
            None,
            debug
        ) as client:
            await callback(client)

    def _start(callback):
        loop.run_until_complete(start(loop, callback))
    return _start


def run():
    def start(callback):
        loop.run_until_complete(callback())
    return start

def _on_close():
    if HttpClient._session._connector:
        HttpClient._session._connector._close() 

    json.dump(CACHE, open(".ed.json", "w"))

signal.signal(signal.SIGTERM, _on_close)
signal.signal(signal.SIGTERM, _on_close)

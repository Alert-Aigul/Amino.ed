import asyncio
from asyncio.events import AbstractEventLoop, get_event_loop

from contextlib import suppress
from time import time
from aiohttp.client import ClientSession
from aiohttp.client_exceptions import WSServerHandshakeError
from aiohttp.client_ws import ClientWebSocketResponse as WSConnection
from eventemitter.emitter import EventEmitter
from ujson import loads

from .utils.helpers import generate_signature
from .utils.models import Auth, Event


class WebSocketClient:
    def __init__(self, auth: Auth, loop: AbstractEventLoop = None) -> None:
        self._session: ClientSession = None
        self._connection: WSConnection = None
        self._loop: AbstractEventLoop = loop or get_event_loop()

        self.auth: Auth = auth
        self.emitter: EventEmitter = EventEmitter()

        self.reconnecting: bool = None
        self.reconnect_cooldown: int = 120
    
    async def run(self):
        self._connection = await self.create_connection()
        self._loop.create_task(self.connection_reciever())

        self.reconnecting = True
        self._loop.create_task(self.reconnecting_task())

    async def connection_reciever(self):
        while True:
            if self._connection.closed:
                await asyncio.sleep(3)
                continue

            with suppress(TypeError):
                recieved_data = await self._connection.receive_json(loads=loads)

                if recieved_data["t"] == 1000:
                    self.emitter.emit("message", Event(**recieved_data["o"]))
                
                self.emitter.emit("event", recieved_data["o"])
                

    async def create_connection(self) -> WSConnection:
        for _ in range(3):
            try:
                self._session = ClientSession()
                data = f"{self.auth.deviceId}|{int(time() * 1000)}"
                url = f"wss://ws3.narvii.com/?signbody={data}"

                headers = {
                    "NDCDEVICEID": self.auth.deviceId,
                    "NDCAUTH": f"sid={self.auth.sid}",
                    "NDC-MSG-SIG": generate_signature(data)
                }

                return await self._session.ws_connect(url, headers=headers)
            except WSServerHandshakeError as e:
                await asyncio.sleep(3)
                await self._session.close()
                print(e)
        
        raise Exception("Websocket connection error.")

    async def close_connection(self) -> None:
        await self._connection.close()
        await self._session.close()

    async def reconnecting_task(self) -> None:
        if self._connection.closed:
            self.create_connection()

        while self.reconnecting:
            await asyncio.sleep(self.reconnect_cooldown)

            if not self._connection.closed:
                await self.close_connection()

            self._connection = await self.create_connection()

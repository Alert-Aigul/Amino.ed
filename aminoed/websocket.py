from time import time
from contextlib import suppress
from asyncio import AbstractEventLoop, sleep
from aiohttp.client import ClientSession
from aiohttp.client_exceptions import WSServerHandshakeError
from aiohttp.client_ws import ClientWebSocketResponse as WSConnection
from eventemitter.emitter import EventEmitter

from .helpers.event import Event
from .helpers.models import Auth
from .helpers.types import EventTypes, allTypes
from .helpers.utils import generate_signature, get_event_loop


class AminoWebSocket:
    def __init__(self, auth: Auth, loop: AbstractEventLoop = None) -> None:
        self._session: ClientSession = None
        self._connection: WSConnection = None
        self._loop: AbstractEventLoop = loop or get_event_loop()

        self.auth: Auth = auth
        self.emitter: EventEmitter = EventEmitter()
        self.event_session = ClientSession()
        
        self.reconnecting: bool = None
        self.reconnect_cooldown: int = 120
        
        self.bot_commands = []
    
    async def run(self):
        self._connection = await self.create_connection()
        self._loop.create_task(self.connection_reciever())

        self.reconnecting = True
        self._loop.create_task(self.reconnecting_task())

    async def connection_reciever(self):
        while True:
            if self._connection.closed:
                await sleep(3)
                continue

            with suppress(TypeError):
                recieved_data = await self._connection.receive_json()

                if recieved_data["t"] == 1000:
                    try:
                    
                        # context = getattr(sys.modules["aminoed"], "Event")
                        
                        event = Event(self.event_session, self.auth, recieved_data["o"])       
                        self.emitter.emit(EventTypes.MESSAGE, event)
                        
                        event_type = f"{event.type}:{event.mediaType}"
                        
                        if event_type in allTypes(EventTypes):
                            self.emitter.emit(event_type, event)
                            
                        if event_type == EventTypes.TEXT_MESSAGE:
                            for command in self.bot_commands:
                                if event.content.lower().startswith(command):
                                    self.emitter.emit(command, event)
                                    
                    except Exception as e:
                        print(e)
                
                elif recieved_data["t"] == 10:
                    self.emitter.emit(EventTypes.NOTIFICATION, recieved_data["o"])
                
                elif recieved_data["t"] == 306 or recieved_data["t"] == 304:
                    self.emitter.emit(EventTypes.ACTION, recieved_data["o"])
                    
                    if recieved_data["o"]["actions"][0] == "Typing":
                        if recieved_data["t"] == 304:
                            self.emitter.emit(EventTypes.USER_TYPING_START, recieved_data["o"])
                            
                        if recieved_data["t"] == 306:
                            self.emitter.emit(EventTypes.USER_TYPING_END, recieved_data["o"])
                
                self.emitter.emit(EventTypes.ANY, recieved_data)
                
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
                await sleep(3)
                await self._session.close()
        
        raise Exception("Websocket connection error.")

    async def close_connection(self) -> None:
        await self._connection.close()
        await self._session.close()

    async def reconnecting_task(self) -> None:
        if self._connection.closed:
            self.create_connection()

        while self.reconnecting:
            await sleep(self.reconnect_cooldown)

            if not self._connection.closed:
                await self.close_connection()

            self._connection = await self.create_connection()

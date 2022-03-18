import asyncio

from typing import Optional
from aiohttp import ClientSession, ClientWebSocketResponse


class GeneratorSocket:
    def __init__(self) -> None:
        self.ws_url = "wss://ed-generators.herokuapp.com/ws"
        self.session: Optional[ClientSession] = None
        self.ws_connection: Optional[ClientWebSocketResponse] = None
 
    async def ws_connect(self) -> ClientWebSocketResponse:
        if not self.session:
            self.session = ClientSession()
 
        return await self.session.ws_connect(self.ws_url)
 
    async def get(self, data: dict):
        if not self.ws_connection:
            self.ws_connection = await self.ws_connect()
            await asyncio.sleep(2.5)
 
        await self.ws_connection.send_str(data)
        return await self.ws_connection.receive_str()

from typing import Any, Optional

from ..client import Client
from .models import Auth, BaseEvent, Message


class Event(BaseEvent):
    def __init__(self, auth: Auth, data) -> None:
        super().__init__(**data, **data["chatMessage"])
        
        self.client: Client = Client(self.ndcId)
        self.client.auth = auth
    
    client: Optional[Any] = None
        
    async def send(
        self, 
        message: str = None,
        mentions: list = None, 
        reply_to_id: str = None,
        type: int = 0
    ) -> Message:
        return await self.client.send_message(
            self.threadId, message, type, reply_to_id, mentions)

    async def reply(
        self,
        message: str = None,
        mentions: list = None,
        type: int = 0
    ) -> Message:
        return await self.client.send_message(
            self.threadId, message, type, self.messageId, mentions)

    async def send_image(self, image: bytes):
        return await self.client.send_image(self.threadId, image)

    async def send_audio(self, audio: bytes):
        return await self.client.send_audio(self.threadId, audio)

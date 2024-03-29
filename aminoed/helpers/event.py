from copy import copy
from typing import Any, Optional, Union

from ..client import Client
from ..http import WebHttpClient
from .models import Auth, BaseEvent, Message

class Event(BaseEvent):
    def __init__(self, auth: Auth, data) -> None:
        super().__init__(**data, **data["chatMessage"])
        
        self.client: Client = Client(self.ndcId, check_updates=False)
        self.client.auth = auth
        self.client.ndc_id = self.ndcId
        
        self.client.ndc_id = self.ndcId
        
        self.web: WebHttpClient = self.client.web
    
    client: Optional[Any] = None
    web: Optional[Any] = None
        
    async def send_message(
        self, 
        message: str = None,
        mentions: list = None, 
        reply_to_id: str = None,
        type: int = 0
    ) -> Message:
        return await self.client.send_message(
            self.threadId, message, type, reply_to_id, mentions)
        
    async def send_web_message(
        self, 
        message: str = None,
        type: int = 0
    ):
        return await self.client.web.send_message(
            self.threadId, message, type)

    async def reply_message(
        self,
        message: str = None,
        mentions: list = None,
        type: int = 0,
        embed_id: str = None,
        embed_type: int = None,
        embed_link: str = None, 
        embed_title: str = None, 
        embed_content: str = None, 
        embed_image: Union[bytes, str] = None
    ) -> Message:
        return await self.client.send_message(
            self.threadId, message, type, self.messageId, mentions,
            embed_id, embed_type, embed_link, embed_title, embed_content, embed_image)
    
    async def send_image(self, image: Union[str, bytes]):
        if isinstance(image, bytes):
            image = await self.client.upload_media(image)
            
        return await self.client.web.send_image(self.threadId, image)

    async def send_audio(self, audio: bytes):
        return await self.client.send_audio(self.threadId, audio)
    
    # async def send_to_user(self, message: str):
    #     return await self.client.web.start_chat([self.uid or self.author.uid], message)
    
    # async def comment_user(self, comment: str):
    #     return await self.client.web.comment_user(self.uid or self.author.uid, comment)

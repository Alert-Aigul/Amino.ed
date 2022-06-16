import io
import sys
import requests

from ujson import loads, JSONDecodeError
from typing import Optional, Tuple

from aiohttp import BaseConnector
from asyncio import AbstractEventLoop, sleep
from zipfile import ZIP_DEFLATED, ZipFile
from eventemitter import EventEmitter

from . import __version__, __title__
from .http import HttpClient
from .helpers.utils import *
from .helpers.exceptions import NoCommunity
from .helpers.types import GLOBAL_ID
from .helpers.models import *
from .websocket import AminoWebSocket


class Client(HttpClient):
    def __init__(
        self,
        ndc_id: Optional[str] = None,
        device_id: Optional[str] = None,
        loop: Optional[AbstractEventLoop] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[str] = None,
        timeout: Optional[int] = None,
        prefix: Optional[str] = None,
        connector: Optional[BaseConnector] = None,
        check_updates: bool = True
    ) -> None:
        super().__init__(ndc_id, None, proxy, proxy_auth, timeout, connector)
        self._loop: Optional[AbstractEventLoop] = loop
        
        self.device_id: str = device_id or self.device_id
        self.emitter: EventEmitter = EventEmitter(self._loop)
        
        self._websocket: Optional[AminoWebSocket] = None
        self.callbacks_to_execute: list = []
        
        self.prefix = prefix or ""
        self.community_info: Optional[Community] = None
        
        if check_updates:
            self.check_updates()
        
    @property
    def loop(self):
        if not self._loop:
            self._loop = get_event_loop()
        return self._loop
    
    @property
    def websocket(self):
        if not self._websocket:
            self._websocket = AminoWebSocket(self.auth)
        return self._websocket

    def set_auth(self, auth: Auth):
        self.auth = auth
        self.websocket.auth = auth
        
        return self   
            
    async def __aenter__(self) -> 'Client':
        return self

    async def __aexit__(self, *args) -> None:
        await self._close_session()

    def __del__(self):
        self.loop.create_task(self._close_session())

    async def _close_session(self):
        if not self.session.closed:
            await self.session.close()
            
    def check_updates(self):
        response = requests.get(f"https://pypi.python.org/pypi/{__title__}/json")
        __newest__ = response.json().get("info", {}).get("version", __version__)
        
        if __version__ != __newest__:
            print(f"New version available: {__newest__} (Using {__version__})")
    
    def with_proxy(
        self, func,
        proxy: str = None, 
        proxy_auth: str = None, 
        timeout: int = None
    ):
        
        async def wrapper(*args, **kwargs):
            nonlocal timeout
                
            if func.__name__  not in self.__dir__():
                raise Exception("Its not a aminoed.Client class method.")
            
            if not asyncio.iscoroutinefunction(func):
                raise Exception("Its not a async function.")

            ndc_id = self.ndc_id
            device_id = self.device_id
            timeout = timeout or self.timeout.total
                        
            ClientClass: "Client" = getattr(sys.modules[__name__], "Client")
            client: "Client" = ClientClass(ndc_id, device_id, None, proxy, proxy_auth, timeout)
   
            client.auth = self.auth
        
            return await (client.__getattribute__(func.__name__)(*args, **kwargs))
        
        return wrapper

    def execute(
        self,
        looping: bool = False,
        start_sleep: float = 0,
        end_sleep: float = 0
    ):
        def _execute(callback):
            if self.auth.sid is not None:
                return self.loop.run_until_complete(callback)
            
            async def execute():
                if not looping:
                    await callback()
                    
                while looping:
                    await sleep(start_sleep)
                    await callback()
                    await sleep(end_sleep)
            
            self.callbacks_to_execute.append(execute)
            
        return _execute

    def on(self, event: str):        
        def callback(callback):
            self.websocket.emitter.on(event, callback)
            
        return callback
    
    def command(
        self, 
        commands: Optional[Union[str, List[str]]] = None, 
        prefix: Optional[str] = None
    ):             
        if isinstance(commands, str):
            commands = [commands]
            
        if prefix is None:
            prefix = self.prefix
            
        def register_handler(callback):
            nonlocal commands
            
            if not commands:
                commands = [callback.__name__]
                
            commands = [f'{prefix}{command}' for command in commands]
            
            for command in commands:
                self.websocket.emitter.on(command, callback)
                self.websocket.bot_commands.append(command)
                
            return callback

        return register_handler
    
    async def set_community(
        self, 
        community: Union[str, int, Community] = GLOBAL_ID
    ) -> 'Client':        
        if isinstance(community, str):
            if community.isdigit():
                self.ndc_id = int(community)
                
            else:
                if "http" not in community and "://" not in community:
                    community = f"https://aminoapps.com/c/{community}"
            
                link_info = await self.get_link_info(community)
                
                self.ndc_id = link_info.community.ndcId
                self.community_info = link_info.community
                
        elif isinstance(community, Community):
            self.community_info = community
            self.ndc_id = community.ndcId
        
        elif isinstance(community, int):
            self.ndc_id = community       
            
        else:
            raise NoCommunity()

        return self
    
    async def login(self, email: str, password: str, device_id: str = None) -> Auth:
        return await self.login_email(email, f"0 {password}", device_id)
    
    async def login_phone(self, phone: str, password: str, device_id: str = None) -> Auth:
        return await self.login_phone(phone, f"0 {password}", device_id)
    
    def start(self, email: str = None, password: str = None, sid: str = None) -> Auth:
        if not sid:
            self.loop.run_until_complete(self.cached_login(email, password))
        else:
            self.loop.run_until_complete(self.login_sid(sid))
        
        for callback in self.callbacks_to_execute:
            self.loop.create_task(callback())
        
        if not (conn := self.websocket._connection) or conn.closed:
            self.websocket.auth = self.auth
            
            self.loop.run_until_complete(self.websocket.run())
            self.loop.run_forever()

        return self.auth
    
    async def cached_login(
        self, 
        email: str, 
        password: str = None
    ) -> Auth:
        try:
            if (auth_json := await get_cache(email, False)):
                auth = Auth(**auth_json)
                
                auth_json["sid"]
                # Calling KeyError if sid not defined
                            
                if not sid_expired(auth.sid):
                    await self.login_sid(auth.sid)
                    
                    self.auth.user = auth.user
                    self.auth.account = auth.account
                    
                    return self.auth
        except KeyError or JSONDecodeError or TypeError:
            print("WARN: Your cache is corrupted and has been deleted to be recreated.")
            os.remove(".ed.cache")
            
        auth = await self.login(email, password)
        await set_cache(email, auth.dict())
        
        return auth
    
    def create_bubble_config(
        self, 
        allowedSlots: list = None, 
        contentInsets: list = None, 
        coverImage: str = None, 
        id: str = None, 
        name: str = None, 
        previewBackgroundUrl: str = None, 
        slots: list = None,
        templateId: str = None, 
        version: int = 1, 
        vertexInset: int = 0,
        zoomPoint: list = None, 
        backgroundPath: str = None, 
        color: str = None, 
        linkColor: str = None
    ) -> ChatBubble.Config:
        bubbleConfig = jsonify(
            allowedSlots=allowedSlots or [{"align":1,"x":5,"y":-5},{"align":2,"x":-30,"y":-5},{"align":4,"x":-30,"y":5},{"align":3,"x":5,"y":5}],
            contentInsets=contentInsets or [26,33,18,49],
            coverImage=coverImage or "http://cb1.narvii.com/7991/fea4e00136e7c0cba79f3b1c0a130d20a12a5624r10-356-160_00.png",
            id=id,
            name=name or "Spring (Template)",
            previewBackgroundUrl=previewBackgroundUrl or "http://cb1.narvii.com/images/6846/96234993898693503497b011ad56c95f028790fa_00.png",
            slots=slots,
            templateId=templateId or "949156e1-cc43-49f0-b9cf-3bbbb606ad6e",
            version=version,
            vertexInset=vertexInset,
            zoomPoint=zoomPoint or [41, 44],
            backgroundPath=backgroundPath or "background.png",
            color=color or "#fff45e",
            linkColor=linkColor or "#74ff32"
        )
        
        return ChatBubble.Config(**bubbleConfig)

    async def generate_bubble_file(self, bubbleImage: bytes = None, bubbleConfig: ChatBubble.Config = None) -> bytes:
        if bubbleImage is None:
            response = await self.session.get(
                "http://cb1.narvii.com/images/6846/eebb8b22237e1b80f46de62284abd0c74cb440f9_00.png")
            bubbleImage = await response.read()

        if not bubbleConfig:
            bubbleConfig = self.create_bubble_config()

        buffer = io.BytesIO()
        with ZipFile(buffer, 'w', ZIP_DEFLATED) as zipfile:
            zipfile.writestr(bubbleConfig.backgroundPath, bubbleImage)
            zipfile.writestr("config.json", bubbleConfig.json())
        return buffer.getvalue()

    def load_bubble(self, bubble_zip: bytes) -> Tuple[bytes, ChatBubble.Config]:
        with ZipFile(io.BytesIO(bubble_zip), 'r') as zipfile:
            config = loads(zipfile.read("config.json"))

            config = ChatBubble.Config(**config)
            background = zipfile.read(config.backgroundPath)
        return background, config

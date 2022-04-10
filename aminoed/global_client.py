import base64
import locale
import io

from typing import BinaryIO, List, Tuple, Union
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile
from aiohttp import ClientSession, ClientTimeout
from time import time, timezone
from eventemitter.emitter import EventEmitter
from ujson import dumps
from asyncio import AbstractEventLoop, get_event_loop

from .utils.models import *
from .utils.types import *
from .utils.helpers import *
from .utils.exceptions import *
from .http_client import AminoHttpClient
from .community_client import CommunityClient
from .websocket import WebSocketClient


class Client(AminoHttpClient):
    def __init__(self,
        loop: Optional[AbstractEventLoop] = None,
        deviceId: Optional[str] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[str] = None
    ) -> None:
            
        self._session: ClientSession = ClientSession(
            timeout=ClientTimeout(60), json_serialize=dumps)
        self._loop: AbstractEventLoop = loop or get_event_loop()

        self.proxy: Optional[str] = proxy
        self.proxy_auth: Optional[str] = proxy_auth
        self.authenticated: bool = False
        self.deviceId: str = deviceId or generate_device_sync()

        self.auth: Auth = Auth(**{})
        self.account: Account = Account(**{})
        self.profile: UserProfile = UserProfile(**{})

        self.emitter: EventEmitter = EventEmitter(self._loop)
        self._websocket: WebSocketClient = WebSocketClient(self.auth, self._loop)
        self.callbacks_to_execute: list = []

    async def __aenter__(self) -> 'Client':
        return self

    async def __aexit__(self, *args) -> None:
        if not self._session.closed:
            await self._session.close()

    def __del__(self):
        self._loop.create_task(self._close_session())

    async def _close_session(self):
        if not self.session.closed:
            await self.session.close()

    def execute(self):
        async def execute(callback):
            if self.authenticated:
                return await callback()

            self.callbacks_to_execute.append(callback)

        def _execute(callback):
            self._loop.run_until_complete(execute(callback))
        return _execute
    
    @property
    def websocket(self):
        if not self._websocket:
            self._websocket = WebSocketClient(self.auth, deviceId=self.deviceId)
        return self._websocket

    def on(self, event: str):        
        def callback(callback):
            self.websocket.emitter.on(event, callback)
        return callback
    
    async def initialize_community(self, comId: str = None, aminoId: str = None, 
            get_info: bool = False, community: Community = None) -> CommunityClient:
        if aminoId:
            comId = (await self.search_community(aminoId))[0].comId

        if get_info:
            community: Community = await self.get_community_info(comId)
        
        if not aminoId and not comId: raise NoCommunity()

        return CommunityClient(comId, self._loop, None,
                community, self.headers, self.proxy, self.proxy_auth)
    
    def run(self, email: str = None, password: str = None, sid: str = None) -> Auth:

        if not sid:
            self._loop.run_until_complete(self.login(email, password))
        else:
            self._loop.run_until_complete(self.login_sid(sid))
        
        for callback in self.callbacks_to_execute:
            self._loop.create_task(callback())
        
        if not (conn := self.websocket._connection) or conn.closed:
            self._loop.run_until_complete(self.websocket.run())
            self._loop.run_forever()

        return self.auth

    async def login(self, email: str, password: str) -> Auth:
        data = {
            "email": email,
            "clientType": 100,
            "secret": f"0 {password}",
            "deviceID": self.deviceId,
            "action": "normal",
            "timestamp": int(time() * 1000)
        }

        response = await self.post("/g/s/auth/login", data)
        self.auth: Auth = Auth(**(await response.json()))
        self.auth.deviceId = self.deviceId
        self.websocket.auth = self.auth

        self.account: Account = self.auth.account
        self.profile: UserProfile = self.auth.userProfile
        
        self.authenticated = True
        self.sid = self.auth.sid
        self.userId = self.auth.auid

        return self.auth
    
    async def logout(self):
        data = {
            "deviceID": self.deviceId,
            "clientType": 100,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/auth/logout", data)

        self.sid = None
        self.auth: Auth = None
        self.account: Account = None
        self.profile: UserProfile = None
        self.authenticated = False
        return response.status
    
    async def get_account_info(self) -> Account:
        response = await self.get(f"/g/s/account")
        return Account(**(await response.json())["account"])
    
    async def get_user_info(self, userId: str) -> UserProfile:
        response = await self.get(f"/g/s/user-profile/{userId}")
        return UserProfile(**(await response.json())["userProfile"])
    
    async def login_sid(self, sid: str) -> Auth:
        self.sid = sid
        self.authenticated = True
        self.userId = sid_to_uid(sid)
        
        self.account: Account = await self.get_account_info()
        self.profile: UserProfile = await self.get_user_info(self.userId)

        self.auth: Auth = Auth(account=self.account, auid=self.userId,
                profile=self.profile, sid=self.sid, deviceId=self.deviceId)
        self.websocket.auth = self.auth
        
        return self.auth
    
    async def register(self, nickname: str, email: str, password: str, code: str) -> Auth:
        data = {
            "secret": f"0 {password}",
            "deviceID": self.deviceId,
            "email": email,
            "clientType": 100,
            "nickname": nickname,
            "latitude": 0,
            "longitude": 0,
            "address": None,
            "type": 1,
            "identity": email,
            "timestamp": int(time() * 1000)
        }

        if code:
            data["validationContext"] = {
                "data": {
                    "code": code
                },
                "type": 1,
                "identity": email
            }

        response = await self.post(f"/g/s/auth/register", data)
        return Auth(**(await response.json()))
    
    async def restore(self, email: str, password: str) -> int:
        data = {
            "secret": f"0 {password}",
            "deviceID": self.deviceId,
            "email": email,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/account/delete-request/cancel", data)
        return response.status
    
    async def configure(self, age: int, genderType: int) -> int:
        if age <= 12:
            raise AgeTooLow()

        data = {
            "age": age,
            "gender": genderType,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/persona/profile/basic", data)
        return response.status
    
    async def verify(self, email: str, code: str) -> int:
        data = {
            "validationContext": {
                "type": 1,
                "identity": email,
                "data": {"code": code}},
            "deviceID": self.deviceId,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/auth/check-security-validation", data)
        return response.status
    
    async def request_verify_code(self, email: str, resetPassword: bool = False) -> int:
        data = {
            "identity": email,
            "type": 1,
            "deviceID": self.deviceId
        }

        if resetPassword:
            data["level"] = 2
            data["purpose"] = "reset-password"

        response = await self.post(f"/g/s/auth/request-security-validation", data)
        print(response.status)
        return response.status
    
    async def activate_account(self, email: str, code: str) -> int:
        data = {
            "type": 1,
            "identity": email,
            "data": {"code": code},
            "deviceID": self.deviceId
        }

        response = await self.post(f"/g/s/auth/activate-email", data)
        return response.status
    
    async def delete_account(self, password: str) -> int:
        data = {
            "deviceID": self.deviceId,
            "secret": f"0 {password}"
        }

        response = await self.post(f"/g/s/account/delete-request", data)
        return response.status

    async def change_password(self, email: str, password: str, code: str) -> int:
        data = {
            "updateSecret": f"0 {password}",
            "emailValidationContext": {
                "data": {
                    "code": code
                },
                "type": 1,
                "identity": email,
                "level": 2,
                "deviceID": self.deviceId
            },
            "phoneNumberValidationContext": None,
            "deviceID": self.deviceId
        }

        response = await self.post(f"/g/s/auth/reset-password", data)
        return response.status

    async def check_device(self, deviceId: str) -> int:
        data = {
            "deviceID": deviceId,
            "bundleID": "com.narvii.amino.master",
            "clientType": 100,
            "timezone": -timezone // 1000,
            "systemPushEnabled": True,
            "locale": locale()[0],
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/device", data)
        return response.status
    
    async def upload_media(self, file: BinaryIO, fileType: str) -> str:
        response = await self.post_content(f"/g/s/media/upload", file.read(), fileType)
        return (await response.json())["mediaValue"]
    
    async def upload_bubble_preview(self, file: BinaryIO) -> str:
        response = await self.post_content(f"{self.api}/g/s/media/upload/target/chat-bubble-thumbnail", file.read(), "image/png")
        return (await response.json())["mediaValue"]
    
    async def get_eventlog(self, language: str = "en") -> dict:
        response = await self.get(f"/g/s/eventlog/profile?language={language}")
        return (await response.json())
    
    async def get_community_info(self, comId: str):
        response = await self.get(f"/g/s-x{comId}/community/info")
        return Community(**(await response.json())["community"])
    
    async def get_account_communities(self, start: int = 0, size: int = 25) -> List[Community]:
        response = await self.get(f"/g/s/community/joined?v=1&start={start}&size={size}")
        return list(map(lambda o: Community(**o), (await response.json())["communityList"])) 
    
    async def search_community(self, aminoId: str):
        response = await self.get(f"/g/s/search/amino-id-and-link?q={aminoId}")

        result = (await response.json())["resultList"]
        if len(await response.text()) == 0: raise CommunityNotFound(aminoId)
        return list(map(lambda o: Community(**o), [com["refObject"] for com in result]))

    async def get_chat_thread(self, chatId: str) -> Thread:
        response = await self.get(f"/g/s/chat/thread/{chatId}")
        return Thread(**(await response.json())["thread"])
    
    async def get_chat_threads(self, start: int = 0, size: int = 25) -> List[Thread]:
        response = await self.get(f"/g/s/chat/thread?type=joined-me&start={start}&size={size}")
        return list(map(lambda o: Thread(**o), (await response.json())["threadList"]))
    
    async def get_chat_users(self, chatId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/g/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2")
        return list(map(lambda o: UserProfile(**o), (await response.json())["memberList"]))
    
    async def start_chat(self, userId: Union[str, list], message: str, title: str = None,
            content: str = None, isGlobal: bool = False, publishToGlobal: bool = False) -> Thread:
        data = {
            "title": title,
            "inviteeUids": userId if isinstance(userId, list) else [userId],
            "initialMessageContent": message,
            "content": content,
            "timestamp": int(time() * 1000)
        }

        if isGlobal: 
            data["type"] = ChatPublishTypes.IS_GLOBAL
            data["eventSource"] = SourceTypes.GLOBAL_COMPOSE
        else: data["type"] = ChatPublishTypes.OFF

        if publishToGlobal: 
            data["publishToGlobal"] = ChatPublishTypes.ON
        else: data["publishToGlobal"] = ChatPublishTypes.OFF

        response = await self.post(f"/g/s/chat/thread", data)
        return Thread(**(await response.json()))
    
    async def join_chat(self, chatId: str) -> int:
        response = await self.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}")
        return response.status

    async def leave_chat(self, chatId: str) -> int:
        response = await self.delete(f"/g/s/chat/thread/{chatId}/member/{self.userId}")
        return response.status

    async def invite_to_chat(self, userId: Union[str, list], chatId: str) -> int:
        data = {
            "uids":  userId if isinstance(userId, list) else [userId],
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/chat/thread/{chatId}/member/invite", data)
        return response.status

    async def kick(self, userId: str, chatId: str, allowRejoin: bool = True) -> int:
        response = await self.delete(f"/g/s/chat/thread/{chatId}/member/{userId}?allowRejoin={allowRejoin}")
        return response.status
    
    async def get_message_info(self, chatId: str, messageId: str):
        response = await self.get(f"/g/s/chat/thread/{chatId}/message/{messageId}")
        return Message(**(await response.json())["message"])
    
    async def get_chat_messages(self, chatId: str, size: int = 25, pageToken: str = None) -> Message:
        if not pageToken: params = f"v=2&pagingType=t&size={size}"
        else: params = f"v=2&pagingType=t&pageToken={pageToken}&size={size}"

        response = await self.get(f"/g/s/chat/thread/{chatId}/message?{params}")
        return list(map(lambda o, p: Message(**o, **p), (js := await response.json())["messageList"], js["paging"]))
    
    async def get_user_following(self, userId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/g/s/user-profile/{userId}/joined?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))

    async def get_user_followers(self, userId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/g/s/user-profile/{userId}/member?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))

    async def get_blocked_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/g/s/block?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))
    
    async def get_blocker_users(self, start: int = 0, size: int = 25) -> List[str]:
        response = await self.get(f"/g/s/block/full-list?start={start}&size={size}")
        return (await response.json())["blockerUidList"]

    async def get_wiki_info(self, wikiId: str) -> Wiki:
        response = await self.get(f"/g/s/item/{wikiId}")
        return Wiki(**(await response.json())["inMyFavorites"])
    
    async def get_blog_info(self, blogId: str) -> Blog:
        response = await self.get(f"/g/s/blog/{blogId}")
        return Blog(**(await response.json())["blog"])
    
    async def get_quiz_info(self, quizId: str) -> Blog:
        response = await self.get(f"/g/s/blog/{quizId}")
        return Blog(**(await response.json())["blog"])
    
    async def get_blog_comments(self, blogId: str, sorting: str = "newest", start: int = 0, size: int = 25) -> List[Comment]:
        response = await self.get(f"/g/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), (await response.json())["commentList"]))
    
    async def get_quiz_comments(self, quizId: str, sorting: str = "newest", start: int = 0, size: int = 25) -> List[Comment]:
        response = await self.get(f"/g/s/blog/{quizId}/comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), (await response.json())["commentList"]))

    async def get_wiki_comments(self, wikiId: str, sorting: str = "newest", start: int = 0, size: int = 25) -> List[Comment]:
        response = await self.get(f"/g/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), (await response.json())["commentList"]))
    
    async def get_wall_comments(self, userId: str, sorting: str, start: int = 0, size: int = 25) -> List[Comment]:
        response = await self.get(f"/g/s/user-profile/{userId}/g-comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), (await response.json())["commentList"]))
    
    async def send_message(self, chatId: str, message: str = None, type: int = 0, replyTo: str = None, 
            mentions: list = None, embedId: str = None, embedType: int = None, embedLink: str = None, 
            embedTitle: str = None, embedContent: str = None, embedImage: Union[BinaryIO, str] = None) -> Message:

        message = message.replace("<$", "‎‏")
        message = message.replace("$>", "‬‭")
        mentions = [{"uid": uid} for uid in mentions if mentions]

        if embedImage:
            if isinstance(embedImage, str):
                embedImage = [[100, embedImage, None]]
            elif isinstance(embedImage, BinaryIO):
                embedImage = [[100, await self.upload_media(embedImage, "image"), None]]
            else:
                raise SpecifyType()

        data = {
            "type": type,
            "content": message,
            "clientRefId": int(time() / 10 % 1000000000),
            "attachedObject": {
                "objectId": embedId,     # ID object (user, blog, and other)
                "objectType": embedType, # ObjectTypes
                "link": embedLink,       # ObjectLink
                "title": embedTitle,     # Embed title
                "content": embedContent, # Embed message
                "mediaList": embedImage  # ObjectPreview
            },
            "extensions": {"mentionedArray": mentions},
            "timestamp": int(time() * 1000)
        }

        if replyTo:
            data["replyMessageId"] = replyTo

        response = await self.post(f"/g/s/chat/thread/{chatId}/message", data)
        return Message(**(await response.json())["message"])
    
    
    async def send_image(self, chatId: str, file: BinaryIO) -> Message:
        data = {
            "type": 0,
            "mediaType": 100,
            "mediaUhqEnabled": True,
            "clientRefId": int(time() / 10 % 1000000000),
            "timestamp": int(time() * 1000)
        }

        data["mediaUploadValueContentType"] = FileTypes.IMAGE
        data["mediaUploadValue"] = base64.b64encode(file.read()).decode()

        response = await self.post(f"/g/s/chat/thread/{chatId}/message", data)
        return Message(**(await response.json())["message"])
    
    async def send_audio(self, chatId: str, file: BinaryIO) -> Message:
        data = {
            "type": 2,
            "mediaType": 110,
            "clientRefId": int(time() / 10 % 1000000000),
            "timestamp": int(time() * 1000)
        }

        data["mediaUploadValueContentType"] = FileTypes.AUDIO
        data["mediaUploadValue"] = base64.b64encode(file.read()).decode()

        response = await self.post(f"/g/s/chat/thread/{chatId}/message", data)
        return Message(**(await response.json())["message"])
    
    async def send_sticker(self, chatId: str, stickerId: str) -> Message:
        data = {
            "type": 3,
            "stickerId": stickerId,
            "clientRefId": int(time() / 10 % 1000000000),
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/chat/thread/{chatId}/message", data)
        return Message(**(await response.json())["message"])
    
    async def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: str = None) -> int:
        data = {
            "adminOpName": 102,
            "adminOpNote": {"content": reason},
            "timestamp": int(time() * 1000)
        }

        if not asStaff:
            response = await self.delete(f"/g/s/chat/thread/{chatId}/message/{messageId}")
            return response.status

        response = await self.post(f"/g/s/chat/thread/{chatId}/message/{messageId}/admin", data)
        return response.status

    async def mark_as_read(self, chatId: str, messageId: str) -> int:
        data = {
            "messageId": messageId,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/chat/thread/{chatId}/mark-as-read", data)
        return response.status
    
    async def edit_chat(self, chatId: str, doNotDisturb: bool = None, pinChat: bool = None, 
            title: str = None, icon: str = None, backgroundImage: BinaryIO = None, content: str = None, 
            announcement: str = None, coHosts: list = None, keywords: list = None, pinAnnouncement: bool = None, 
            publishToGlobal: bool = None, canTip: bool = None, viewOnly: bool = None, canInvite: bool = None, fansOnly: bool = None) -> int:
        data = {"timestamp": int(time() * 1000)}
        responses = []

        if title: data["title"] = title
        if content: data["content"] = content
        if icon: data["icon"] = icon
        if keywords: data["keywords"] = keywords
        if announcement: data["extensions"] = {"announcement": announcement}
        if pinAnnouncement: data["extensions"] = {"pinAnnouncement": pinAnnouncement}
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}

        if publishToGlobal: data["publishToGlobal"] = 0
        if not publishToGlobal: data["publishToGlobal"] = 1

        if coHosts:
            data = {"uidList": coHosts, "timestamp": int(time() * 1000)}
            response = await self.post(f"/g/s/chat/thread/{chatId}/co-host", data)
            responses.append(response.status)

        if doNotDisturb is True:
            data = {"alertOption": 2, "timestamp": int(time() * 1000)}
            response = await self.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}/alert", data)
            responses.append(response.status)

        if doNotDisturb is False:
            data = {"alertOption": 1, "timestamp": int(time() * 1000)}
            response = await self.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}/alert", data)
            responses.append(response.status)

        if backgroundImage:
            data = {"media": [100, await self.upload_media(backgroundImage, "image"), None], "timestamp": int(time() * 1000)}
            response = await self.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}/background", data)
            responses.append(response.status)
        
        if pinChat is True: responses.append((await self.post(f"/g/s/chat/thread/{chatId}/pin", data)).status)
        if pinChat is False: responses.append((await self.post(f"/g/s/chat/thread/{chatId}/unpin", data)).status)

        if viewOnly is True: responses.append((await self.post(f"/g/s/chat/thread/{chatId}/view-only/enable", data)).status)
        if viewOnly is False: responses.append((await self.post(f"/g/s/chat/thread/{chatId}/view-only/disable", data)).status)

        if canInvite is True: responses.append((await self.post(f"/g/s/chat/thread/{chatId}/members-can-invite/enable", data)).status)
        if canInvite is False: responses.append((await self.post(f"/g/s/chat/thread/{chatId}/members-can-invite/disable", data)).status)

        if canTip is True: responses.append((await self.post(f"/g/s/chat/thread/{chatId}/tipping-perm-status/enable", data)).status)
        if canTip is False: responses.append((await self.post(f"/g/s/chat/thread/{chatId}/tipping-perm-status/disable", data)).status)

        responses.append((await self.post(f"/g/s/chat/thread/{chatId}", data)).status)
        return int(sum(responses) / len(responses))
    
    async def send_coins(self, coins: int, blogId: str = None,
            chatId: str = None, objectId: str = None, transactionId: str = None) -> int:
        data = {
            "coins": coins,
            "tippingContext": {
                "transactionId": transactionId or str(uuid4())
            },
            "timestamp": int(time() * 1000)
        }

        if blogId:
            response = await self.post(f"/g/s/blog/{blogId}/tipping", data)
            return response.status
        
        elif chatId:
            response = await self.post(f"/g/s/chat/thread/{chatId}/tipping", data)
            return response.status
        
        elif objectId:
            data["objectId"] = objectId
            data["objectType"] = ObjectTypes.ITEM
            response = await self.post(f"/g/s/tipping", data)
            return response.status
        
        else: SpecifyType()        
    
    async def follow(self, userId: Union[str, list]):
        if isinstance(userId, str):
            response = await self.post(f"/g/s/user-profile/{userId}/member")
            return response.status

        elif isinstance(userId, list):
            data = {"targetUidList": userId, "timestamp": int(time() * 1000)}
            response = await self.post(f"/g/s/user-profile/{self.userId}/joined", data)
            return response.status

        else: raise WrongType(type(userId))

    async def unfollow(self, userId: str) -> int:
        response = await self.delete(f"/g/s/user-profile/{userId}/member/{self.userId}")
        return response.status
    
    async def block(self, userId: str) -> int:
        response = await self.post(f"/g/s/block/{userId}", None)
        return response.status

    async def unblock(self, userId: str) -> int:
        response = await self.delete(f"/g/s/block/{userId}")
        return response.status
    
    async def flag(self, reason: str, flagType: int, userId: str = None,
            blogId: str = None, wikiId: str = None, comId: str = None) -> int:
        if reason is None: raise ReasonNeeded
        if flagType is None: raise FlagTypeNeeded

        data = {
            "flagType": flagType,
            "message": reason,
            "timestamp": int(time() * 1000)
        }

        if userId:
            data["objectId"] = userId
            data["objectType"] = ObjectTypes.USER

        elif blogId:
            data["objectId"] = blogId
            data["objectType"] = ObjectTypes.BLOG

        elif wikiId:
            data["objectId"] = wikiId
            data["objectType"] = ObjectTypes.ITEM
        
        elif comId:
            data["objectId"] = comId
            data["objectType"] = ObjectTypes.COMMUNITY

        else: raise SpecifyType

        if self.authenticated: flg = "flag"
        else: flg = "g-flag"

        if comId: place = f"x{comId}"
        else: place = "g"

        response = await self.post(f"/{place}/s/{flg}", data)
        return response.status
    
    async def link_identify(self, code: str) -> dict:
        response = await self.get(f"/g/s/community/link-identify?q=http%3A%2F%2Faminoapps.com%2Finvite%2F{code}")
        return response.json()
    
    async def join_community(self, comId: str, invitationCode: str = None) -> int:
        data = {"timestamp": int(time() * 1000)}
        if invitationCode: data["invitationId"] = await self.link_identify(invitationCode)

        response = await self.post(f"/x{comId}/s/community/join", data)
        return response.status

    async def request_join_community(self, comId: str, message: str = None) -> int:
        data = {
            "message": message, 
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{comId}/s/community/membership-request", data)
        return response.status

    async def leave_community(self, comId: str) -> int:
        response = await self.post(f"/x{comId}/s/community/leave")
        return response.status

    async def edit_profile(self, nickname: str = None, content: str = None, icon: Union[str, BinaryIO] = None,
            backgroundColor: str = None, backgroundImage: Union[str, BinaryIO] = None, defaultBubbleId: str = None) -> int:
        data = {
            "address": None,
            "latitude": 0,
            "longitude": 0,
            "mediaList": None,
            "eventSource": SourceTypes.USER_PROFILE,
            "timestamp": int(time() * 1000)
        }

        if content: data["content"] = content
        if nickname: data["nickname"] = nickname            
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if defaultBubbleId: data["extensions"] = {"defaultBubbleId": defaultBubbleId}

        if icon:
            if isinstance(icon, str):
                data["icon"] = icon

            if isinstance(icon, BinaryIO):
                data["icon"] = await self.upload_media(icon, "image")

            else: raise SpecifyType()

        if backgroundImage:
            if isinstance(backgroundImage, str):
                data["extensions"] = {"style": {
                    "backgroundMediaList": [[100, backgroundImage, None, None, None]]}}

            if isinstance(backgroundImage, BinaryIO):
                image = await self.upload_media(backgroundImage, "image")
                data["extensions"] = {"style": {"backgroundMediaList": [[100, image, None, None, None]]}}

            else: raise SpecifyType()

        response = await self.post(f"/g/s/user-profile/{self.userId}", data)
        return response.status
    
    async def set_privacy_status(self, isAnonymous: bool = False, getNotifications: bool = False) -> int:
        data = {"timestamp": int(time() * 1000)}

        if not isAnonymous: data["privacyMode"] = 1
        if isAnonymous: data["privacyMode"] = 2

        if not getNotifications: data["notificationStatus"] = 2
        if getNotifications: data["privacyMode"] = 1

        response = await self.post(f"/g/s/account/visit-settings", data)
        return response.status

    async def set_amino_id(self, aminoId: str) -> int:
        data = {"aminoId": aminoId, "timestamp": int(time() * 1000)}

        response = await self.post(f"/g/s/account/change-amino-id", data)
        return response.status
    
    async def get_linked_communities(self, userId: str) -> List[Community]:
        response = await self.get(f"/g/s/user-profile/{userId}/linked-community")
        return list(map(lambda o: Community(**o), (await response.json())["linkedCommunityList"]))

    async def get_unlinked_communities(self, userId: str) -> List[Community]:
        response = await self.get(f"/g/s/user-profile/{userId}/linked-community")
        return list(map(lambda o: Community(**o), (await response.json())["unlinkedCommunityList"]))

    async def reorder_linked_communities(self, comIds: list) -> int:
        data = {"ndcIds": comIds, "timestamp": int(time() * 1000)}
        response = await self.post(f"/g/s/user-profile/{self.userId}/linked-community/reorder", data)
        return response.status

    async def add_linked_community(self, comId: str) -> int:
        response = await self.post(f"/g/s/user-profile/{self.userId}/linked-community/{comId}")
        return response.status

    async def remove_linked_community(self, comId: str) -> int:
        response = await self.delete(f"/g/s/user-profile/{self.userId}/linked-community/{comId}")
        return response.status
    
    async def comment(self, message: str, userId: str = None, 
            blogId: str = None, wikiId: str = None, replyTo: str = None) -> int:
        data = {
            "content": message,
            "stickerId": None,
            "type": 0,
            "timestamp": int(time() * 1000)
        }

        if replyTo:
            data["respondTo"] = replyTo

        if userId:
            data["eventSource"] = SourceTypes.USER_PROFILE
            response = await self.post(f"/g/s/user-profile/{userId}/g-comment", data)
            return response.status

        elif blogId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/g/s/blog/{blogId}/g-comment", data)
            return response.status

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/g/s/item/{wikiId}/g-comment", data)
            return response.status

        else: raise SpecifyType()
    
    async def delete_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
        if userId:
            url = f"/g/s/user-profile/{userId}/g-comment/{commentId}"

        elif blogId:
            url = f"/g/s/blog/{blogId}/g-comment/{commentId}"

        elif wikiId:
            url = f"/g/s/item/{wikiId}/g-comment/{commentId}"

        else: raise SpecifyType()

        response = await self.delete(url)
        return response.status
    
    async def like_blog(self, blogId: Union[str, list] = None, wikiId: str = None) -> int:
        data = {
            "value": 4,
            "timestamp": int(time() * 1000)
        }

        if blogId:
            if isinstance(blogId, str):
                data["eventSource"] = SourceTypes.USER_PROFILE
                response = await self.post(f"/g/s/blog/{blogId}/g-vote?cv=1.2", data)
                return response.status

            elif isinstance(blogId, list):
                data["targetIdList"] = blogId
                response = await self.post(f"/g/s/feed/g-vote", data)
                return response.status

            else: raise WrongType(type(blogId))

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/g/s/item/{wikiId}/g-vote?cv=1.2", data)
            return response.status

        else: raise SpecifyType()
    
    async def unlike_blog(self, blogId: str = None, wikiId: str = None) -> int:
        if blogId:
            url = f"/g/s/blog/{blogId}/g-vote?eventSource=UserProfileView"

        elif wikiId:
            url = f"/g/s/item/{wikiId}/g-vote?eventSource=PostDetailView"

        else: raise SpecifyType()

        response = await self.delete(url)
        return response.status
    
    async def like_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
        data = {
            "value": 4,
            "timestamp": int(time() * 1000)
        }

        if userId:
            data["eventSource"] = SourceTypes.USER_PROFILE
            response = await self.post(f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
            return response.status

        elif blogId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
            return response.status

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/g/s/item/{wikiId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
            return response.status

        else: raise SpecifyType()
    
    async def unlike_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
        if userId: 
            url = f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView"

        elif blogId: 
            url = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView"

        elif wikiId: 
            url = f"/g/s/item/{wikiId}/comment/{commentId}/g-vote?eventSource=PostDetailView"

        else: raise SpecifyType()

        response = await self.delete(url)
        return response.status
    
    async def get_membership_info(self) -> Membership:
        response = await self.get(f"/g/s/membership?force=true")
        return Membership(**(await response.json()))

    async def get_ta_announcements(self, lang: str = "en", start: int = 0, size: int = 25) -> List[Blog]:
        response = await self.get(f"/g/s/announcement?language={lang}&start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))

    async def get_wallet_info(self) -> Wallet:
        response = await self.get(f"/g/s/wallet")
        return Wallet(**(await response.json())["wallet"])

    async def get_wallet_history(self, start: int = 0, size: int = 25) -> List[Transaction]:
        response = await self.get(f"/g/s/wallet/coin/history?start={start}&size={size}")
        return list(map(lambda o: Transaction(**o), (await response.json())["coinHistoryList"]))

    async def get_from_device(self, deviceId: str) -> str:
        response = await self.get(f"/g/s/auid?deviceId={deviceId}")
        return (await response.json())["auid"]

    async def get_link_info(self, code: str) -> Link:
        response = await self.get(f"/g/s/link-resolution?q={code}")
        return Link(**(ext := (await response.json())["linkInfoV2"]["extensions"]), **ext.get("linkInfo", {}))
    
    async def get_from_id(self, objectId: str, objectType: int, comId: str = None) -> Link:
        data = {
            "objectId": objectId,
            "targetCode": 1,
            "objectType": objectType,
            "timestamp": int(time() * 1000)
        }

        if comId: url = f"/g/s/link-resolution"
        else: url = f"/g/s-x{comId}/link-resolution"

        response = await self.post(url, data)
        return Link(**(await response.json())["linkInfoV2"]["extensions"])
    
    async def get_supported_languages(self):
        response = await self.get(f"/g/s/community-collection/supported-languages?start=0&size=100")
        return (await response.text())["supportedLanguages"]

    async def claim_new_user_coupon(self):
        response = await self.post(f"/g/s/coupon/new-user-coupon/claim")
        return response.status

    async def get_subscriptions(self, start: int = 0, size: int = 25):
        response = await self.get(f"/g/s/store/subscription?objectType=122&start={start}&size={size}")
        return (await response.text())["storeSubscriptionItemList"]

    async def get_all_users(self, start: int = 0, size: int = 25):
        response = await self.get(f"/g/s/user-profile?type=recent&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), await response.json()))

    async def accept_host(self, chatId: str, requestId: str):
        response = await self.post(f"/g/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept")
        return response.status

    async def invite_to_vc(self, chatId: str, userId: str):
        data = {"uid": userId}
        response = await self.post(f"/g/s/chat/thread/{chatId}/vvchat-presenter/invite", data)
        return response.status

    async def wallet_config(self, level: int):
        data = {
            "adsLevel": level,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s/wallet/ads/config", data)
        return response.status

    async def get_avatar_frames(self, start: int = 0, size: int = 25):
        response = await self.get(f"/g/s/avatar-frame?start={start}&size={size}")
        return list(map(lambda o: AvatarFrame(**o), (await response.json())["avatarFrameList"]))
    
    async def subscribe_amino_plus(self, transactionId = "", sku="d940cf4a-6cf2-4737-9f3d-655234a92ea5"):
        data = {
            {
                "sku": sku,
                "packageName": "com.narvii.amino.master",
                "paymentType": 1,
                "paymentContext": {
                    "transactionId": (transactionId or str(uuid4())),
                    "isAutoRenew": True
                },
                "timestamp": time()
            }
        }

        response = await self.post(f"/g/s/membership/product/subscribe", data)
        return response.status
    
    async def change_avatar_frame(self, frameId: str, aplyToAll: bool = False) -> int:
        data = {
            "frameId": frameId,
            "applyToAll": 1 if aplyToAll else 0,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"{self.apip}/g/s/avatar-frame/apply", data)
        return response.status
    
    def create_bubble_config(self, allowedSlots: list = None, contentInsets: list = None, coverImage: str = None, id: str = None, name: str = None, previewBackgroundUrl: str = None, slots: list = None,
        templateId: str = None, version: int = 1, vertexInset: int = 0, zoomPoint: list = None, backgroundPath: str = None, color: str = None, linkColor: str = None) -> ChatBubble.Config:
        bubbleConfig = {
            "allowedSlots": allowedSlots or [{"align":1,"x":5,"y":-5},{"align":2,"x":-30,"y":-5},{"align":4,"x":-30,"y":5},{"align":3,"x":5,"y":5}],
            "contentInsets": contentInsets or [26,33,18,49],
            "coverImage": coverImage or "http://cb1.narvii.com/7991/fea4e00136e7c0cba79f3b1c0a130d20a12a5624r10-356-160_00.png",
            "id": id,
            "name": name or "Spring (Template)",
            "previewBackgroundUrl": previewBackgroundUrl or "http://cb1.narvii.com/images/6846/96234993898693503497b011ad56c95f028790fa_00.png",
            "slots": slots,
            "templateId": templateId or "949156e1-cc43-49f0-b9cf-3bbbb606ad6e",
            "version": version,
            "vertexInset": vertexInset,
            "zoomPoint": zoomPoint or [41, 44],
            "backgroundPath": backgroundPath or "background.png",
            "color": color or "#fff45e",
            "linkColor": linkColor or "#74ff32"
        }
        return ChatBubble.Config(**bubbleConfig)

    async def generate_bubble_file(self, bubbleImage: BinaryIO = None, bubbleConfig: ChatBubble.Config = None) -> BinaryIO:
        if bubbleImage is None:
            response = await self.get("http://cb1.narvii.com/images/6846/eebb8b22237e1b80f46de62284abd0c74cb440f9_00.png")
            bubbleImage = io.BytesIO(await response.read())

        if not bubbleConfig:
            bubbleConfig = self.create_bubble_config()

        buffer = io.BytesIO()
        with ZipFile(buffer, 'w', ZIP_DEFLATED) as zipfile:
            zipfile.writestr(bubbleConfig.backgroundPath, bubbleImage.read())
            zipfile.writestr("config.json", bubbleConfig.json())
        return buffer

    def load_bubble(self, bubble_zip: BinaryIO) -> Tuple[bytes, ChatBubble]:
        with ZipFile(bubble_zip, 'r') as zipfile:
            config = loads(zipfile.read("config.json"))

            config = ChatBubble.Config(config)
            background = zipfile.read(config.backgroundPath)
        return background, config

    async def change_chat_bubble(self, bubbleId: str, chatId: str = None) -> int:
        data = {
            "bubbleId": bubbleId,
            "applyToAll": 0 if chatId else 1,
            "threadId": chatId if chatId else None,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"{self.api}/g/s/chat/thread/apply-bubble", data)
        return response.status
    
    async def get_chat_bubbles(self, chatId: str, start: int = 25, size: int = 25) -> List[ChatBubble]:
        response = await self.get(f"{self.api}/g/s/chat/chat-bubble?type=all-my-bubbles?threadId={chatId}?start={start}?size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["chatBubbleList"]))
    
    async def get_chat_bubble(self, bubbleId: str) -> ChatBubble:
        response = await self.get(f"{self.api}/g/s/chat/chat-bubble/{bubbleId}")
        return ChatBubble(**(response.text)["chatBubble"])

    async def get_chat_bubble_templates(self, start: int = 0, size: int = 25) -> List[ChatBubble]:
        response = await self.get(f"{self.api}/g/s/chat/chat-bubble/templates?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["templateList"]))
    
    async def generate_chat_bubble(self, bubble: BinaryIO = None, templateId: str = "949156e1-cc43-49f0-b9cf-3bbbb606ad6e") -> ChatBubble:
        response = await self.post(f"{self.api}/g/s/chat/chat-bubble/templates/{templateId}/generate", bubble)
        return ChatBubble(**(response.text)["chatBubble"])
    
    async def edit_chat_bubble(self, bubbleId: str, bubble: BinaryIO) -> ChatBubble:
        response = await self.post(f"{self.api}/g/s/chat/chat-bubble/{bubbleId}", bubble)
        return ChatBubble(**(response.text)["chatBubble"])

import json
import sys

from random import randint
from uuid import uuid4
from time import time
from locale import localeconv
from base64 import b64encode
from typing import Dict, List, Optional, Union

from aiohttp import BaseConnector, BasicAuth, ClientSession, ClientTimeout, ContentTypeError
from json_minify import json_minify

from .helpers.models import *

from .helpers.types import GLOBAL_ID, ChatPublishTypes, ContentTypes, FeaturedTypes, Language, ObjectTypes, PathTypes, PostTypes, RepairTypes, SourceTypes, UserTypes
from .helpers.utils import generate_signature, generate_device, get_ndc, jsonify, update_device
from .helpers.exceptions import CheckException, IpTomporaryBan, SpecifyType, HtmlError


class WebHttpClient:
    URL = "https://aminoapps.com/"
    
    def __init__(
        self,
        ndc_id: Optional[int] = None,
        sid: Optional[str] = None,
        session: Optional[ClientSession] = None,
        connector: Optional[BaseConnector] = None,
        debug: bool = False
    ) -> None:
        self.connector: Optional[BaseConnector] = connector
        self.session: ClientSession = session or ClientSession()
        self.debug = debug
        self.debug = debug
        
        self.sid: Optional[str] = sid
        self.ndc_id: int = ndc_id or GLOBAL_ID
        
        user_agent = "Amino.ed Python/{0[0]}.{0[1]} Bot"
        self.user_agent: str = user_agent.format(sys.version_info)
    
    @property
    def referer(self):
        return f"{self.URL}/partial/main-chat-window?ndcId={self.ndc_id}"
        
    async def request(self, method: str, path: str, **kwargs):
        url = f"{self.URL}api{path}"

        headers: Dict[str, str] = {
            "User-Agent": self.user_agent,
            "x-requested-with": "xmlhttprequest",
            "cookie": f"sid={self.sid}",
            "referer": self.referer,
            "host": "aminoapps.com"
        }
            
        if kwargs.get("json") is not None:
            headers["Content-Type"] = ContentTypes.JSON

            data = kwargs.pop("json")
            data["ndcId"] = get_ndc(self.ndc_id)[1:-2]

            kwargs["data"] = json.dumps(data)
        
        kwargs["headers"] = headers
        response_json: Optional[Dict] = None

        async with self.session.request(method, url, **kwargs) as response:
            try:
                response_json: Dict = await response.json(loads=json.loads)
            except ContentTypeError:
                response_text = await response.text()
                raise HtmlError(response_text)
            
            if self.debug:
                message = f"\n\n<---REQUEST {url} START--->\n\n"
                message += json.dumps(headers) + "\n"
                
                if data is not None:
                    message += data + "\n"
            
                message += f"\n{response.status} {json.dumps(response_json)}\n\n"
                message += f"<---REQUEST {url} END--->\n\n"
                print(message, end="")

            if response.status != 200:
                if not self.session.closed:
                    await self.session.close()

                return CheckException(response_json)
            
            print(response.status, response_json)

            return response_json or response.status

    async def send_message(self, thread_id: str, message: str, type: int = 0):
        data = jsonify(
            threadId=thread_id,
            message=jsonify(
                content=message,
                mediaType=0,
                type=type,
                sendFailed=False,
                clientRefId=0
            )
        )

        return await self.request("POST", f"/add-chat-message", json=data)
    
    # image - upload image link
    async def send_image(self, thread_id: str, image: str):        
        data = jsonify(
            threadId=thread_id,
            message=jsonify(
                content=None,
                mediaType=100,
                type=0,
                sendFailed=False,
                clientRefId=0,
                mediaValue=image
            )
        )

        return await self.request("POST", f"/add-chat-message", json=data)
    
    async def join_chat(self, thread_id: str):
        data = jsonify(threadId=thread_id)
        return await self.request("POST", f"/join-thread", json=data)
    
    async def leave_chat(self, thread_id: str):
        data = jsonify(threadId=thread_id)
        return await self.request("POST", "/leave-thread", json=data)
    
    async def follow(self, uid: str):
        data = jsonify(followee_id=uid)
        return await self.request("POST", "/follow-user", json=data)
    
    async def start_chat(self, uids: list, message: str = None):
        data = jsonify(inviteeUids=uids, initialMessageContent=message, type=0)
        return await self.request("POST", "/create-chat-thread", json=data)
    
    async def comment_blog(self, blog_id: str, comment: str):
        data = jsonify(content=comment, postType=PostTypes.BLOG, postId=blog_id)
        return await self.request("POST", "/submit_comment", json=data)
    
    async def comment_user(self, uid: str, comment: str):
        data = jsonify(content=comment, postType=PostTypes.USER, postId=uid)
        return await self.request("POST", "/submit_comment", json=data)
    
    async def comment_wiki(self, wiki_id: str, comment: str):
        data = jsonify(content=comment, postType=PostTypes.WIKI, postId=wiki_id)
        return await self.request("POST", "/submit_comment", json=data)
    

class HttpClient:
    URL: str = "https://service.aminoapps.com/"
    LANGUAGE: str = Language.ENG
    _session: ClientSession = ClientSession()

    def __init__(
        self,
        ndc_id: Optional[int] = None,
        session: Optional[ClientSession] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[BasicAuth] = None,
        timeout: Optional[int] = None,
        connector: Optional[BaseConnector] = None,
        debug: bool = False
    ) -> None:
        self.connector: Optional[BaseConnector] = connector
        self._session: Optional[ClientSession] = session or self._session
        self.debug = debug

        self.ndc_id: int = GLOBAL_ID
        self._auth: Auth = Auth(**{})
        self._device_id: str = generate_device()
        
        if ndc_id is not None:
            self.ndc_id: int = ndc_id
            
        self.timeout: Optional[ClientTimeout] = ClientTimeout(timeout or 10)
            
        self.proxy: Optional[str] = proxy
        self.proxy_auth: Optional[BasicAuth] = proxy_auth

        self.user_agent: str = "Apple iPhone12,1 iOS v15.5 Main/3.12.2"
        
    async def request(self, method: str, path: str, **kwargs):
        ndc_id = kwargs.pop("ndc_id", self.ndc_id)
        url = f"{self.URL}api/v1{get_ndc(ndc_id)}{path}"
            
        if kwargs.pop("full_url", None):
            url = kwargs.get("full_url", url)

        headers: Dict[str, str] = {
            "User-Agent": self.user_agent,
            "NDCDEVICEID": self.device_id,
            "Accept-Language": self.LANGUAGE,
            "Content-Type": ContentTypes.URL_ENCODED
        }

        if self.auth.sid is not None:
            headers["NDCAUTH"] = "sid=" + self.auth.sid

        if kwargs.get("json") is not None:
            data = kwargs.pop("json")
            data["timestamp"] = int(time() * 1000)

            kwargs["data"] = json.dumps(data)
        
        if (data := kwargs.get("data")) is not None:
            headers["NDC-MSG-SIG"] = generate_signature(data)
        
        if kwargs.get("content_type") is not None:
            headers["Content-Type"] = kwargs.pop("content_type")

        if kwargs.get("proxy") is None:
            kwargs["proxy"] = self.proxy

        if kwargs.get("proxy_auth") is None:
            kwargs["proxy_auth"] = self.proxy_auth
        
        kwargs["headers"] = headers
        response_json: Optional[Dict] = None

        async with self.session.request(method, url, **kwargs) as response:
            try:
                response_json: Dict = await response.json(loads=json.loads)
            except ContentTypeError:
                response_text = await response.text()
                
                if not self.session.closed:
                    await self.session.close()
                
                if "403" in response_text:
                    raise IpTomporaryBan("403 Forbidden")
                else:
                    raise HtmlError(response_json)
                
            if self.debug:
                message = f"\n\n<---REQUEST {url} START--->\n\n"
                message += json.dumps(headers) + "\n"
                
                if data is not None:
                    message += data + "\n"
            
                message += f"\n{response.status} {json.dumps(response_json)}\n\n"
                message += f"<---REQUEST {url} END--->\n\n"
                print(message, end="")

            if response.status != 200:
                if not self.session.closed:
                    await self.session.close()

                return CheckException(response_json)
            return response_json or response.status
    
    @property
    def web(self) -> WebHttpClient:
        return WebHttpClient(self.ndc_id, self.auth.sid, self.session)
        
    @property
    def session(self) -> ClientSession:
        if not self._session or self._session.closed:
            self._session = ClientSession(
                timeout=self.timeout, connector=self.connector)
        return self._session
    
    @session.setter
    def session(self, session: ClientSession) -> None:
        self._session = session
        
    @property
    def ndc_id(self) -> str:
        if not self._ndc_id:
            self._ndc_id = GLOBAL_ID
        return self._ndc_id
    
    @ndc_id.setter
    def ndc_id(self, ndc_id: int) -> None:
        if isinstance(ndc_id, str):
            raise Exception("ndc_id can only be a int")
        
        self._ndc_id = ndc_id
        
    @property
    def auth(self) -> Auth:
        if not self._auth:
            self._auth = Auth({})
        return self._auth
    
    @auth.setter
    def auth(self, auth: Auth):
        self._auth = auth 

    @property
    def device_id(self):
        return self._device_id

    @device_id.setter
    def device_id(self, device_id: str):
        self._device_id = update_device(device_id)

    async def base_login(
        self, 
        email: str = None, 
        password: str = None, 
        device_id: str = None, 
        phoneNumber: str = None
    ) -> Auth:
        data = jsonify(
            email=email,
            secret=password,
            clientType=100,
            deviceID=device_id or self.device_id,
            action="normal",
            v=2
        )
        
        if phoneNumber:
            data["phoneNumber"] = phoneNumber

        response = Auth(**(await self.request("POST", "/auth/login", json=data, ndc_id=GLOBAL_ID)))
        self.auth = response
        self.auth.deviceId = self.device_id

        return self.auth

    async def logout(self, remove_auth: bool = True) -> Dict:
        data = jsonify(
            deviceID=self.device_id,
            clientType=100
        )

        response = await self.request("POST", "/auth/logout", json=data, ndc_id=GLOBAL_ID)
        self.auth = Auth(**{}) if remove_auth else self.auth

        return response
    
    async def get_account_info(self) -> Account:
        response = await self.request("GET", "/account", ndc_id=GLOBAL_ID)
        return Account(**response["account"])
    
    async def get_user_info(self, uid: str) -> UserProfile:
        response = await self.request("GET", f"/user-profile/{uid}")
        return UserProfile(**response["userProfile"])

    async def register(self, nickname: str, email: str,
                    password: str, code: str = None) -> Auth:
        data = jsonify(
            secret=f"0 {password}",
            deviceID=self.device_id,
            email=email,
            clientType=100,
            nickname=nickname,
            latitude=0,
            longitude=0,
            address=None,
            type=1,
            identity=email
        )

        if code:
            data["validationContext"] = jsonify(
                data=jsonify(code=code),
                type=1, identify=email
            )

        return Auth(**(await self.request("POST", "/auth/register", json=data, ndc_id=GLOBAL_ID)))
    
    async def restore(self, email: str, password: str) -> Dict:
        data = jsonify(
            secret=f"0 {password}",
            deviceID=self.device_id,
            email=email
        )

        return await self.request("POST",
            "/account/delete-request/cancel", json=data, ndc_id=GLOBAL_ID)
    
    async def configure(self, age: int, gender_type: int) -> Dict:
        data = jsonify(age=age, gender=gender_type)

        return await self.request("POST",
            "/persona/profile/basic", json=data, ndc_id=GLOBAL_ID)
    
    async def verify(self, email: str, code: str) -> Dict:
        data = jsonify(
            validationContext=jsonify(
                type=1, identity=email,
                data=jsonify(code=code)),
            deviceID=self.device_id
        )

        return await self.request("POST",
            "/auth/check-security-validation", json=data, ndc_id=GLOBAL_ID)

    async def request_verify_code(self, email: str, reset_password: bool = False) -> int:
        data = jsonify(
            type=1,
            identity=email,
            deviceID=self.device_id
        )

        if reset_password:
            data.update(jsonify(
                level=2,
                purpose="reset-password"
            ))

        return await self.request("POST",
            "/auth/request-security-validation", json=data, ndc_id=GLOBAL_ID)

    
    async def activate_account(self, email: str, code: str) -> int:
        data = jsonify(
            type=1, identity=email,
            data=jsonify(code=code),
            deviceID=self.device_id
        )

        return await self.request("POST",
            "/auth/activate-email", json=data, ndc_id=GLOBAL_ID)

    
    async def delete_account(self, password: str) -> int:
        data = jsonify(
            deviceID=self.device_id,
            secret=f"0 {password}"
        )

        return await self.request("POST",
            "/account/delete-request", json=data, ndc_id=GLOBAL_ID)
    
    async def change_password(self, email: str, password: str, code: str) -> int:
        data = jsonify(
            updateSecret=f"0 {password}",
            emailValidationContext=jsonify(
                data=jsonify(code=code),
                type=1,
                identity=email,
                level=2,
                deviceID=self.device_id
            ),
            phoneNumberValidationContext=None,
            deviceID=self.device_id
        )

        return await self.request("POST", "/auth/reset-password", json=data, ndc_id=GLOBAL_ID)

    async def check_device(self, device_id: str) -> int:
        data = jsonify(
            deviceID=device_id,
            bundleID="com.narvii.amino.master",
            clientType=100,
            timezone=(0),
            systemPushEnabled=True,
            locale=localeconv()[0]
        )

        return await self.request("POST", "/device", json=data, ndc_id=GLOBAL_ID)
    
    async def upload_media(self, file: bytes, content_type: str = ContentTypes.JPG) -> str:
        response = await self.request("POST", "/media/upload",
                data=file, content_type=content_type)

        return response["mediaValue"]
    
    async def upload_themepack_raw(self, file: bytes):
        response = await self.request("POST", f"/media/upload/target/community-theme-pack", data=file)
        return response
    
    async def upload_bubble_preview(self, file: bytes) -> str:
        response = await self.request("POST",
            "/media/upload/target/chat-bubble-thumbnail",
            data=file, content_type=ContentTypes.PNG)
            
        return response["mediaValue"]
    
    async def get_eventlog(self, language: str = "en") -> Dict:
        return await self.request("GET", f"/eventlog/profile?language={language}", ndc_id=GLOBAL_ID)
    
    async def get_community_info(self, ndc_id: int = None) -> Community:
        response = await self.request("GET", "/community/info?withInfluencerList=1" \
            "&withTopicList=true&influencerListOrderStrategy=fansCount", ndc_id=-(ndc_id or self.ndc_id))

        return Community(**response["community"])
    
    async def get_account_communities(self, start: int = 0, size: int = 100) -> List[Community]:
        response = await self.request("GET", f"/community/joined?v=1&start={start}&size={size}", ndc_id=GLOBAL_ID)
        return list(map(lambda o: Community(**o), response["communityList"])) 
    
    async def search_community(self, amino_id: str):
        response = await self.request("GET", f"/search/amino-id-and-link?q={amino_id}", ndc_id=GLOBAL_ID)
        return list(map(lambda o: Community(**o), [v["refObject"] for v in response["resultList"]]))

    async def get_chat_thread(self, thread_id: str) -> Thread:
        return Thread(**(await self.request("GET", f"/chat/thread/{thread_id}"))["thread"])
    
    async def get_chat_threads(self, start: int = 0, size: int = 100) -> List[Thread]:
        response = await self.request("GET",
            f"/chat/thread?type=joined-me&start={start}&size={size}")

        return list(map(lambda o: Thread(**o), response["threadList"]))
    
    async def get_chat_users(self, thread_id: str, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET",
            f"/chat/thread/{thread_id}/member?start={start}&size={size}&type=default&cv=1.2")

        return list(map(lambda o: UserProfile(**o), response["memberList"]))
    
    async def start_chat(self, uid: Union[str, list], message: str, title: str = None,
            content: str = None, is_global: bool = False, publish_to_global: bool = False) -> Thread:
            
        data = jsonify(
            title=title, initialMessageContent=message, content=content,
            inviteeUids=uid if isinstance(uid, list) else [uid] 
        )

        if is_global:
            data.update(jsonify(
                type=ChatPublishTypes.IS_GLOBAL,
                eventSource=SourceTypes.GLOBAL_COMPOSE
            ))
        else:
            data["type"] = ChatPublishTypes.OFF

        if publish_to_global: 
            data["publishToGlobal"] = ChatPublishTypes.ON
        else:
            data["publishToGlobal"] = ChatPublishTypes.OFF

        return Thread(**(await self.request("POST", f"/chat/thread", json=data)))
    
    async def join_chat(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/member/{self.auth.auid}")

    async def leave_chat(self, thread_id: str) -> int:
        return await self.request("DELETE", f"/chat/thread/{thread_id}/member/{self.auth.auid}")

    async def invite_to_chat(self, uid: Union[str, list], thread_id: str) -> int:
        data = jsonify(uids=uid if isinstance(uid, list) else [uid])
        return await self.request("POST", f"/chat/thread/{thread_id}/member/invite", json=data)

    async def kick(self, uid: str, thread_id: str, allow_rejoin: bool = True) -> int:
        return await self.request("DELETE", f"/chat/thread/{thread_id}/member/{uid}?allowRejoin={0 if allow_rejoin else 1}")
    
    async def get_message_info(self, thread_id: str, message_id: str):
        return Message(**(await self.request("GET", f"/chat/thread/{thread_id}/message/{message_id}"))["message"])

    async def get_chat_messages(self, thread_id: str, size: int = 100, page_token: str = None) -> List[Message]:
        if not page_token: params = f"v=2&pagingType=t&size={size}"
        else: params = f"v=2&pagingType=t&pageToken={page_token}&size={size}"

        response = await self.request("GET", f"/chat/thread/{thread_id}/message?{params}")
        return list(map(lambda o: Message(**o, **response.get("paging", {})),  response["messageList"]))
    
    async def get_user_following(self, uid: str, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-profile/{uid}/joined?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))

    async def get_user_followers(self, uid: str, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-profile/{uid}/member?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))

    async def get_blocked_users(self, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/block?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_blocker_users(self, start: int = 0, size: int = 100) -> List[str]:
        response = await self.request("GET", f"/block/full-list?start={start}&size={size}")
        return response["blockerUidList"]

    async def get_wiki_info(self, wiki_id: str) -> Wiki:
        return Wiki(**(await self.request("GET", f"/item/{wiki_id}"))["item"])
    
    async def get_blog_info(self, blog_id: str) -> Blog:
        return Blog(**(await self.request("GET", f"/blog/{blog_id}"))["blog"])
    
    async def get_blog_comments(self, blog_id: str, sorting: str = "newest", start: int = 0, size: int = 100) -> List[Comment]:
        response = await self.request("GET", f"/blog/{blog_id}/comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), response["commentList"]))

    async def get_wiki_comments(self, wiki_id: str, sorting: str = "newest", start: int = 0, size: int = 100) -> List[Comment]:
        response = await self.request("GET", f"/item/{wiki_id}/comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), response["commentList"]))
    
    async def get_wall_comments(self, uid: str, sorting: str, start: int = 0, size: int = 100) -> List[Comment]:
        response = await self.request("GET", f"/user-profile/{uid}/g-comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), response["commentList"]))
    
    async def send_message(self, thread_id: str, message: str = None, type: int = 0, reply_to_id: str = None, 
            mentions: list = None, embed_id: str = None, embed_type: int = None, embed_link: str = None, 
            embed_title: str = None, embed_content: str = None, embed_image: Union[bytes, str] = None) -> Message:

        message = message.replace("<$", "‎‏")
        message = message.replace("$>", "‬‭")
        
        if mentions is not None:
            mentions = [{"uid": uid} for uid in mentions if mentions]

        if embed_image:
            if isinstance(embed_image, str):
                embed_image = [[100, embed_image, None]]

            elif isinstance(embed_image, bytes):
                embed_image = [[100, await self.upload_media(embed_image), None]]

            else:
                raise SpecifyType()

        data = jsonify(
            type=type,
            content=message,
            attachedObject=jsonify(
                objectId=embed_id,     # ID object (user, blog, and other)
                objectType=embed_type, # ObjectTypes
                link=embed_link,       # ObjectLink
                title=embed_title,     # Embed title
                content=embed_content, # Embed message
                mediaList=embed_image  # ObjectPreview
            ),
            clientRefId=int(time() / 10 % 1000000000),
            extensions=jsonify(mentionedArray=mentions)
        )

        if reply_to_id:
            data["replyMessageId"] = reply_to_id

        response = await self.request("POST",
            f"/chat/thread/{thread_id}/message", json=data)
            
        return Message(**response["message"])
    
    
    async def send_image(self, thread_id: str, file: bytes) -> Message:
        data = jsonify(
            type=0,
            mediaType=100,
            mediaUhqEnabled=True,
            clientRefId=int(time() / 10 % 1000000000),
            
            mediaUploadValueContentType=ContentTypes.JPG,
            mediaUploadValue=b64encode(file).decode()
        )        

        response = await self.request("POST", f"/chat/thread/{thread_id}/message", json=data)
        return Message(**response["message"])
    
    async def send_audio(self, thread_id: str, file: bytes) -> Message:
        data = jsonify(
            type=2,
            mediaType=110,
            mediaUhqEnabled=True,
            clientRefId=int(time() / 10 % 1000000000),
            
            mediaUploadValueContentType=ContentTypes.AAC,
            mediaUploadValue=b64encode(file).decode()
        )

        response = await self.request("POST",
            f"/chat/thread/{thread_id}/message", data)

        return Message(**response["message"])
    
    async def send_sticker(self, thread_id: str, sticker_id: str) -> Message:
        data = jsonify(
            type=3, stickerId=sticker_id,
            clientRefId=int(time() / 10 % 1000000000)
        )

        response = await self.request("POST", f"/chat/thread/{thread_id}/message", json=data)
        return Message(**response["message"])
    

    async def delete_message(self, thread_id: str, message_id: str, as_staff: bool = False, reason: str = None) -> int:
        data = jsonify(adminOpName=102, adminOpNote=jsonify(content=reason))

        if not as_staff:
            return await self.request("DELETE", f"/chat/thread/{thread_id}/message/{message_id}")

        return await self.request("POST", f"/chat/thread/{thread_id}/message/{message_id}/admin", json=data)

    async def mark_as_read(self, thread_id: str, message_id: str) -> int:
        data = jsonify(messageId=message_id)
        return await self.request("POST", f"/chat/thread/{thread_id}/mark-as-read", json=data)

    async def edit_chat(self, thread_id: str, title: str = None, icon: str = None, content: str = None, 
                announcement: str = None, keywords: list = None, pin_announcement: bool = None, 
                publish_to_global: bool = None, fans_only: bool = None) -> int:
        data = jsonify(
            title=title,
            content=content,
            icon=icon,
            keywords=keywords,
            extensions=jsonify(
                announcement=announcement,
                pinAnnouncement=pin_announcement,
                fansOnly=fans_only
            ),
            publishToGlobal=0 if publish_to_global else 1
        )

        return await self.request("POST", f"/chat/thread/{thread_id}", json=data)

    async def set_chat_hosts(self, co_hosts: list, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/co-host", json=jsonify(uidList=co_hosts))
    
    async def chat_dustrub_enable(self, thread_id: str) -> int:
        return await self.request("POST",
            f"/chat/thread/{thread_id}/member/{self.auth.auid}/alert",
            json=jsonify(alertOption=1))
    
    async def chat_dustrub_disable(self, thread_id: str) -> int:
        return await self.request("POST",
            f"/chat/thread/{thread_id}/member/{self.auth.auid}/alert",
            json=jsonify(alertOption=2))

    async def set_chat_background(self, background_image: Union[str, bytes], thread_id: str) -> int:
        if isinstance(background_image, bytes):
            data = jsonify(media=[100, await self.upload_media(background_image), None])

        elif isinstance(background_image, str):
            data = jsonify(media=[100, background_image, None])
        
        else:
            raise SpecifyType()

        return await self.request("POST",
            f"/chat/thread/{thread_id}/member/{self.auth.auid}/background", json=data)

    async def pin_chat(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/pin", json={})
    
    async def unpin_chat(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/unpin", json={})
    
    async def chat_view_only_enable(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/view-only/enable", json={})

    async def chat_view_only_disble(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/view-only/disable", json={})

    async def chat_invite_members_enable(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/members-can-invite/enable", json={})

    async def chat_invite_members_disable(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/members-can-invite/disable", json={})

    async def chat_tipping_enable(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/tipping-perm-status/enable", json={})

    async def chat_tipping_disable(self, thread_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/tipping-perm-status/disable", json={})

    async def send_coins_to_blog(self, coins: int, blog_id: str, transaction_id: str = None) -> int:
        data = jsonify(coins=coins, tippingContext=jsonify(transactionId=transaction_id or str(uuid4())))

        return await self.request("POST", f"/blog/{blog_id}/tipping", json=data)
    
    async def send_coins_to_chat(self, coins: int, thread_id: str, transaction_id: str = None) -> int:
        data = jsonify(coins=coins, tippingContext=jsonify(transactionId=transaction_id or str(uuid4())))
        
        return await self.request("POST", f"/chat/thread/{thread_id}/tipping", json=data)

    async def send_coins_to_wiki(self, coins: int, objectId: str, transaction_id: str = None) -> int:
        data = jsonify(coins=coins, objectId=objectId, objectType=ObjectTypes.ITEM,
            tippingContext=jsonify(transactionId=transaction_id or str(uuid4())))
        
        return await self.request("POST", f"/tipping", json=data)
    
    async def follow_one_user(self, uid: str):
        return await self.request("POST", f"/user-profile/{uid}/member")

    async def follow_many_users(self, uid: list):
        data = jsonify(targetUidList=uid)
        return await self.request("POST", f"/user-profile/{self.auth.auid}/joined", json=data)

    async def unfollow_user(self, uid: str) -> int:
        return await self.request("DELETE", f"/user-profile/{uid}/member/{self.auth.auid}")
    
    async def block_user(self, uid: str) -> int:
        return await self.request("POST", f"/block/{uid}", json={})

    async def unblock_user(self, uid: str) -> int:
        return await self.request("DELETE", f"/block/{uid}")

    async def flag_user(self, reason: str, flag_type: int, uid: str) -> int:
        data = jsonify(
            flagType=flag_type,
            message=reason,
            objectId=uid,
            objectType=ObjectTypes.USER
        )

        return await self.request("POST", "/flag", json=data)

    async def flag_blog(self, reason: str, flag_type: int, blog_id: str) -> int:
        data = jsonify(
            flagType=flag_type,
            message=reason,
            objectId=blog_id,
            objectType=ObjectTypes.BLOG
        )

        return await self.request("POST", "/flag", json=data)

    async def flag_wiki(self, reason: str, flag_type: int, wiki_id: str) -> int:
        data = jsonify(
            flagType=flag_type,
            message=reason,
            objectId=wiki_id,
            objectType=ObjectTypes.ITEM
        )

        return await self.request("POST", "/flag", json=data)

    async def flag_community(self, reason: str, flag_type: int, ndc_id: int = None) -> int:
        data = jsonify(
            flagType=flag_type,
            message=reason,
            objectId=ndc_id or self.ndc_id,
            objectType=ObjectTypes.ITEM
        )

        return await self.request("POST", "/flag", json=data)

    async def link_identify(self, code: str) -> Dict:
        return await self.request("GET", f"/community/link-identify?q=http://aminoapps.com/invite/{code}")
    
    async def join_community(self, invitation_code: str = None, ndc_id: int = None) -> int:
        data = {}

        if invitation_code:
            data = jsonify(invitationId=await self.link_identify(invitation_code))

        return await self.request("POST", "/community/join", json=data, ndc_id=ndc_id or self.ndc_id)

    async def request_join_community(self, message: str = None, ndc_id: int = None) -> int:
        data = jsonify(message=message)

        return await self.request("POST", "/community/membership-request", 
                                  json=data, ndc_id=ndc_id or self.ndc_id)

    async def leave_community(self, ndc_id: int = None) -> int:
        return await self.request("POST", "/community/leave", ndc_id=ndc_id or self.ndc_id)
    
    async def edit_profile(self, nickname: str = None, content: str = None, icon: Union[str, bytes] = None,
            background_color: str = None, background_image: Union[str, bytes] = None, default_bubble_id: str = None, titles: list = None) -> int:
        data = jsonify(
            address=None, latitude=0,
            longitude=0,mediaList=None,
            eventSource=SourceTypes.USER_PROFILE
        )

        if content:
            data["content"] = content

        if nickname:
            data["nickname"] = nickname    
                
        if background_color:
            data["extensions"] = jsonify(style=jsonify(backgroundColor=background_color))

        if default_bubble_id:
            data["extensions"] = jsonify(style=jsonify(defaultBubbleId=default_bubble_id))

        if titles:
            data["extensions"] = jsonify(customTitles=titles)

        if icon:
            if isinstance(icon, str):
                data["icon"] = icon

            elif isinstance(icon, bytes):
                data["icon"] = await self.upload_media(icon)

            else:
                raise SpecifyType()

        if background_image:
            if isinstance(background_image, str):
                data["extensions"] = jsonify(style=jsonify(backgroundMediaList=[[100, background_image, None, None, None]]))

            elif isinstance(background_image, bytes):
                background_image = await self.upload_media(background_image)
                data["extensions"] = jsonify(style=jsonify(backgroundMediaList=[[100, background_image, None, None, None]]))

            else:
                raise SpecifyType()

        return await self.request("POST", f"/user-profile/{self.auth.auid}", json=data)

    async def get_linked_communities(self, uid: str) -> List[Community]:
        response = await self.request("GET", f"/user-profile/{uid}/linked-community", ndc_id=GLOBAL_ID)
        return list(map(lambda o: Community(**o), response["linkedCommunityList"]))

    async def get_unlinked_communities(self, uid: str) -> List[Community]:
        response = await self.request("GET", f"/user-profile/{uid}/linked-community", ndc_id=GLOBAL_ID)
        return list(map(lambda o: Community(**o), response["unlinkedCommunityList"]))

    async def reorder_linked_communities(self, ndc_ids: list) -> int:
        data = jsonify(ndcIds=ndc_ids)
        return await self.request("POST", f"/user-profile/{self.auth.auid}/linked-community/reorder", json=data)

    async def add_linked_community(self, ndc_id: int = None) -> int:
        return await self.request("POST", f"/user-profile/{self.auth.auid}/linked-community/{ndc_id or self.ndc_id}")

    async def remove_linked_community(self, ndc_id: int = None) -> int:
        return await self.request("DELETE", f"/user-profile/{self.auth.auid}/linked-community/{ndc_id or self.ndc_id}")

    async def set_privacy_status(self, is_anonymous: bool = False, get_notifications: bool = False) -> int:
        data = jsonify(
            privacyMode=2 if is_anonymous else 1,
            notificationStatus=1 if get_notifications else 2
        )

        return await self.request("POST", f"/account/visit-settings", json=data)

    async def set_amino_id(self, amino_id: str) -> int:
        data = jsonify(aminoId=amino_id)

        return await self.request("POST", f"/account/change-amino-id", json=data)

    async def comment_blog(self, message: str, blog_id: str, reply_to_id: str = None) -> int:
        data = jsonify(
            content=message, stickerId=None,
            type=0, eventSource=SourceTypes.DATAIL_POST
        )
        
        if reply_to_id:
            data["respondTo"] = reply_to_id

        return await self.request("POST", f"/blog/{blog_id}/g-comment", json=data)
    
    async def comment_wiki(self, message: str, wiki_id: str, reply_to_id: str = None) -> int:
        data = jsonify(
            content=message, stickerId=None,
            type=0, eventSource=SourceTypes.DATAIL_POST
        )

        if reply_to_id:
            data["respondTo"] = reply_to_id

        return await self.request("POST", f"/item/{wiki_id}/g-comment", json=data)

    async def comment_profile(self, message: str, uid: str, reply_to_id: str = None) -> int:
        data = jsonify(
            content=message, stickerId=None,
            type=0, eventSource=SourceTypes.USER_PROFILE
        )

        if reply_to_id:
            data["respondTo"] = reply_to_id

        return await self.request("POST", f"/user-profile/{uid}/g-comment", json=data)

    async def delete_comment(self, comment_id: str, blog_id: str) -> int:
        return await self.request("DELETE", f"/blog/{blog_id}/g-comment/{comment_id}")
    
    async def delete_comment(self, comment_id: str, wiki_id: str) -> int:
        return await self.request("DELETE", f"/item/{wiki_id}/g-comment/{comment_id}")

    async def delete_comment(self, comment_id: str, uid: str) -> int:
        return await self.request("DELETE", f"/user-profile/{uid}/g-comment/{comment_id}")

    async def like_wiki_comment(self, comment_id: str, wiki_id: str) -> int:
        data = jsonify(value=4, eventSource=SourceTypes.DATAIL_POST)
        return await self.request("POST", f"/item/{wiki_id}/comment/{comment_id}/g-vote?cv=1.2&value=1", json=data)

    async def like_blog_comment(self, comment_id: str, blog_id: str) -> int:
        data = jsonify(value=4, eventSource=SourceTypes.DATAIL_POST)
        return await self.request("POST", f"/blog/{blog_id}/comment/{comment_id}/g-vote?cv=1.2&value=1", json=data)

    async def like_profile_comment(self, comment_id: str, uid: str) -> int:
        data = jsonify(value=4, eventSource=SourceTypes.USER_PROFILE)
        return await self.request("POST", f"/user-profile/{uid}/comment/{comment_id}/g-vote?cv=1.2&value=1", json=data)
    
    async def unlike_profile_comment(self, comment_id: str, uid: str) -> int:
        return await self.request("DELETE", f"/user-profile/{uid}/comment/{comment_id}/g-vote?eventSource={SourceTypes.USER_PROFILE}")

    async def unlike_blog_comment(self, comment_id: str, blog_id: str) -> int:
        return await self.request("DELETE", f"/blog/{blog_id}/comment/{comment_id}/g-vote?eventSource={SourceTypes.DATAIL_POST}")

    async def unlike_wiki_comment(self, comment_id: str, wiki_id: str) -> int:
        return await self.request("DELETE", f"/item/{wiki_id}/comment/{comment_id}/g-vote?eventSource={SourceTypes.DATAIL_POST}")

    async def like_many_blogs(self, blog_ids: list) -> int:
        data = jsonify(value=4, targetIdList=blog_ids, eventSource=SourceTypes.USER_PROFILE)
        return await self.request("POST", f"/feed/g-vote", json=data)

    async def like_one_blog(self, blog_id: str) -> int:
        data = jsonify(value=4, eventSource=SourceTypes.USER_PROFILE)
        return await self.request("POST", f"/blog/{blog_id}/g-vote?cv=1.2", json=data)

    async def like_wiki(self, wiki_id: str) -> int:
        data = jsonify(value=4, eventSource=SourceTypes.DATAIL_POST)
        return await self.request("POST", f"/item/{wiki_id}/g-vote?cv=1.2", json=data)
    
    async def unlike_blog(self, blog_id: str) -> int:
        return await self.request("DELETE", f"/blog/{blog_id}/g-vote?eventSource={SourceTypes.USER_PROFILE}")

    async def unlike_wiki(self, wiki_id: str) -> int:
        return await self.request("DELETE", f"/item/{wiki_id}/g-vote?eventSource={SourceTypes.DATAIL_POST}")

    async def get_membership_info(self) -> Membership:
        response = await self.request("GET", "/membership?force=true")
        return Membership(**response)

    async def get_ta_announcements(self, lang: str = "en", start: int = 0, size: int = 100) -> List[Blog]:
        response = await self.request("GET", f"/announcement?language={lang}&start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))

    async def get_wallet_info(self) -> Wallet:
        response = await self.request("GET", "/wallet")
        return Wallet(**response["wallet"])

    async def get_wallet_history(self, start: int = 0, size: int = 100) -> List[Transaction]:
        response = await self.request("GET", f"/wallet/coin/history?start={start}&size={size}")
        return list(map(lambda o: Transaction(**o), response["coinHistoryList"]))

    async def get_from_device(self, device_id: str) -> str:
        return (await self.request("GET", f"/auid?deviceId={device_id}"))["auid"]

    async def get_link_info(self, code: str) -> Link:
        response = await self.request("GET", f"/link-resolution?q={code}", ndc_id=GLOBAL_ID)
        return Link(**(ext := response["linkInfoV2"]["extensions"]), **ext.get("linkInfo", {}))

    async def get_from_id(self, object_id: str, object_type: int, ndc_id: int = None) -> Link:
        data = jsonify(objectId=object_id, targetCode=1, objectType=object_type)

        response = await self.request("POST", f"/link-resolution", json=data, ndc_id=-(ndc_id or self.ndc_id))
        return Link(**(ext := response["linkInfoV2"]["extensions"]), **ext.get("linkInfo", {}))

    async def get_supported_languages(self):
        return (await self.request("GET", "/community-collection/supported-languages?start=0&size=100"))["supportedLanguages"]

    async def claim_new_user_coupon(self):
        return await self.request("POST", "/coupon/new-user-coupon/claim")

    async def get_subscriptions(self, start: int = 0, size: int = 100):
        return (await self.request("GET",
            f"/store/subscription?objectType={ObjectTypes.SUBSCRIPTION}&start={start}&size={size}"))["storeSubscriptionItemList"]

    async def get_all_users(self, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-profile?type={UserTypes.RECENT}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_community_leaders(self, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-profile?type={UserTypes.LEADERS}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_community_curators(self, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-profile?type={UserTypes.CURATORS}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_banned_users(self, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-profile?type={UserTypes.BANNED}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_featured_users(self, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-profile?type={UserTypes.FEATURED}d&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"])) 
    
    async def accept_host(self, thread_id: str, request_id: str):
        return await self.request("POST", f"/chat/thread/{thread_id}/transfer-organizer/{request_id}/accept")

    async def invite_to_vc(self, thread_id: str, uid: str):
        return await self.request("POST", f"/chat/thread/{thread_id}/vvchat-presenter/invite", json=jsonify(uid=uid))

    async def get_chat_bubbles(self, thread_id: str, start: int = 0, size: int = 100) -> List[ChatBubble]:
        response = await self.request("GET", f"/chat/chat-bubble?type=all-my-bubbles?threadId={thread_id}?start={start}?size={size}")
        return list(map(lambda o: UserProfile(**o), response["chatBubbleList"]))
    
    async def get_chat_bubble(self, bubble_id: str) -> ChatBubble:
        response = await self.request("GET", f"/chat/chat-bubble/{bubble_id}")
        return ChatBubble(**response["chatBubble"])

    async def get_chat_bubble_templates(self, start: int = 0, size: int = 100) -> List[ChatBubble]:
        response = await self.request("GET", f"/chat/chat-bubble/templates?start={start}&size={size}")
        return list(map(lambda o: ChatBubble(**o), response["templateList"]))
    
    async def generate_chat_bubble(self, bubble: bytes = None, template_id: str = "949156e1-cc43-49f0-b9cf-3bbbb606ad6e") -> ChatBubble:
        response = await self.request("POST", f"/chat/chat-bubble/templates/{template_id}/generate", bubble, content_type=ContentTypes.OCTET_STREAM)
        return ChatBubble(**response["chatBubble"])
    
    async def edit_chat_bubble(self, bubble_id: str, bubble: bytes) -> ChatBubble:
        response = await self.request("POST", f"/chat/chat-bubble/{bubble_id}", data=bubble, content_type=ContentTypes.OCTET_STREAM)
        return ChatBubble(**response["chatBubble"])

    async def get_avatar_frames(self, start: int = 0, size: int = 100):
        response = await self.request("GET", f"/avatar-frame?start={start}&size={size}")
        return list(map(lambda o: AvatarFrame(**o), response["avatarFrameList"]))

    async def change_chat_bubble(self, bubble_id: str, thread_id: str = None) -> int:
        data = jsonify(
            bubbleId=bubble_id,
            applyToAll=0 if thread_id else 1,
            threadId=thread_id if thread_id else None
        )

        return await self.request("POST", "/chat/thread/apply-bubble", json=data)

    async def wallet_config(self, level: int):
        data = jsonify(adsLevel=level)
        return await self.request("POST", "/wallet/ads/config", json=data)
    
    async def subscribe_amino_plus(self, transaction_id = None, sku="d940cf4a-6cf2-4737-9f3d-655234a92ea5"):
        data = jsonify(
            sku=sku, packageName="com.narvii.amino.master", paymentType=1,
            paymentContext=jsonify(transactionId=(transaction_id or str(uuid4())), isAutoRenew=True)
        )

        return await self.request("POST", "/membership/product/subscribe", json=data)
    
    async def change_avatar_frame(self, frame_id: str, aply_to_all: bool = False) -> int:
        data = jsonify(
            frameId=frame_id,
            applyToAll=0 if aply_to_all else 1
        )

        return await self.request("POST", "/avatar-frame/apply", json=data)

    async def get_invite_codes(self, ndc_id: int = None, status: str = "normal", start: int = 0, size: int = 100) -> List[InviteCode]:
        response = await self.request("GET", f"/community/invitation?status={status}&start={start}&size={size}", ndc_id=-(ndc_id or self.ndc_id))
        return list(map(lambda o: InviteCode(**o), response["communityInvitationList"]))

    async def generate_invite_code(self, ndc_id: int = None, duration: int = 0, force: bool = True):
        data = jsonify(duration=duration, force=force)

        response = await self.request("POST", f"/community/invitation", json=data, ndc_id=-(ndc_id or self.ndc_id))
        return InviteCode(**response["communityInvitation"])

    async def delete_invite_code(self, invite_id: str, ndc_id: int = None) -> int:
        return await self.request("DELETE", f"/community/invitation/{invite_id}", ndc_id=-(ndc_id or self.ndc_id))
    
    async def delete_blog(self, blog_id: str) -> int:
        return await self.request("DELETE", f"/blog/{blog_id}")

    async def delete_wiki(self, wiki_id: str) -> int:
        return await self.request("DELETE", f"/item/{wiki_id}")

    async def post_blog(self, title: str, content: str, image_list: list = None, caption_list: list = None, 
            categoriesList: list = None, background_color: str = None, fans_only: bool = False, extensions: Dict = None) -> int:

        data = jsonify(
            address=None,
            content=content,
            title=title,
            extensions=extensions,
            latitude=0,
            longitude=0,
            eventSource=SourceTypes.GLOBAL_COMPOSE
        )
        
        if caption_list and image_list:
            data["mediaList"] = [[100, await self.upload_media(image), caption] 
                                 for image, caption in zip(image_list, caption_list)]

        elif image_list:
            data["mediaList"] = [[100, await self.upload_media(image), None] for image in image_list]

        if fans_only:
            data["extensions"] = jsonify(fansOnly=fans_only)

        if background_color:
            data["extensions"] = jsonify(style=jsonify(backgroundColor=background_color))

        if categoriesList:
            data["taggedBlogCategoryIdList"] = categoriesList

        return await self.request("POST", f"/blog", json=data)
    
    async def post_wiki(self, title: str, content: str, icon: str = None, imageList: list = None,
            keywords: str = None, background_color: str = None, fans_only: bool = False) -> int:

        mediaList = [[100, await self.upload_media(image), None] for image in imageList]

        data = jsonify(
            label=title,
            content=content,
            mediaList=mediaList,
            eventSource=SourceTypes.GLOBAL_COMPOSE
        )

        if icon:
            data["icon"] = icon

        if keywords:
            data["keywords"] = keywords
        
        if fans_only:
            data["extensions"] = jsonify(fansOnly=fans_only)

        if background_color:
            data["extensions"] = jsonify(style=jsonify(backgroundColor=background_color))

        return await self.request("POST", f"/item", json=data)

    async def edit_blog(self, blogId: str, title: str = None, content: str = None, imageList: list = None, 
            categoriesList: list = None, background_color: str = None, fans_only: bool = False) -> int:
        mediaList = [[100, await self.upload_media(image), None] for image in imageList]

        data = jsonify(
            address=None,
            mediaList=mediaList,
            latitude=0,
            longitude=0,
            eventSource=SourceTypes.DATAIL_POST
        )

        if title:
            data["title"] = title

        if content:
            data["content"] = content
        
        if fans_only:
            data["extensions"] = jsonify(fansOnly=fans_only)

        if background_color:
            data["extensions"] = jsonify(style=jsonify(backgroundColor=background_color))

        if categoriesList:
            data["taggedBlogCategoryIdList"] = categoriesList

        return await self.request("POST", f"/blog/{blogId}", json=data)
    
    async def repost_blog(self, content: str, blog_id: str) -> int:
        data = jsonify(
            content=content,
            refObjectId=blog_id,
            refObjectType=ObjectTypes.BLOG,
            type=2
        )

        return await self.request("POST", f"/blog", json=data)

    async def repost_wiki(self, content: str, wiki_id: str) -> int:
        data = jsonify(
            content=content,
            refObjectId=wiki_id,
            refObjectType=ObjectTypes.ITEM,
            type=2
        )

        return await self.request("POST", f"/blog", json=data)

    async def check_in(self, timezone: int = 0) -> CheckIn:
        data = jsonify(timezone=timezone)

        response = await self.request("POST", f"/check-in", json=data)
        return CheckIn(**response)

    async def repair_check_in(self, method: int = RepairTypes.COINS) -> int:
        data = jsonify(repairMethod=method)
        return await self.request("POST", f"/check-in/repair", json=data)

    async def lottery(self, timezone: int = 0) -> int:
        data = jsonify(timezone=timezone)

        response = await self.request("POST", f"/check-in/lottery", json=data)
        return Lottery(**response["lotteryLog"])
      
    async def vote_poll(self, blog_id: str, option_id: str) -> int:
        data = jsonify(value=1, eventSource=SourceTypes.DATAIL_POST)
        return await self.request("POST", f"/blog/{blog_id}/poll/option/{option_id}/vote", json=data)
    
    async def upvote_comment(self, blog_id: str, comment_id: str) -> int:
        data = jsonify(value=1, eventSource=SourceTypes.DATAIL_POST)
        return await self.request("POST", f"/blog/{blog_id}/comment/{comment_id}/vote?cv=1.2&value=1", json=data)

    async def downvote_comment(self, blog_id: str, comment_id: str) -> int:
        data = jsonify(value=-1, eventSource=SourceTypes.DATAIL_POST)
        return await self.request("POST", f"/blog/{blog_id}/comment/{comment_id}/vote?cv=1.2&value=-1", json=data)

    async def unvote_comment(self, blog_id: str, comment_id: str) -> int:
        return await self.request("DELETE", f"/blog/{blog_id}/comment/{comment_id}/vote?eventSource=PostDetailView")

    async def activity_status(self, status: int, mood_sticker_id: str = None, duration: int = 86400) -> int:
        data = jsonify(onlineStatus=status, duration=duration, moodStickerId=mood_sticker_id)
        return await self.request("POST", f"/user-profile/{self.auth.auid}/online-status", json=data)
    
    async def check_notifications(self) -> int:
        return await self.request("POST", f"/notification/checked")

    async def delete_notification(self, notification_id: str) -> int:
        return await self.request("DELETE", f"/notification/{notification_id}")

    async def clear_notifications(self) -> int:
        return await self.request("DELETE", f"/notification")
    
    async def invite_many_to_chat(self, uids: list, thread_id: str) -> int:
        data = jsonify(uids=uids)
        return await self.request("POST", f"/chat/thread/{thread_id}/member/invite", json=data)

    async def invite_one_to_chat(self, uid: str, thread_id: str) -> int:
        data = jsonify(uids=[uid])
        return await self.request("POST", f"/chat/thread/{thread_id}/member/invite", json=data)

    async def add_to_favorites(self, uid: str) -> int:
        return await self.request("POST", f"/user-group/quick-access/{uid}")

    async def thank_tip(self, thread_id: str, uid: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/tipping/tipped-users/{uid}/thank")
    
    async def transfer_organizer(self, thread_id: str, uids: list) -> int:
        data = jsonify(uidList=uids)
        return await self.request("POST", f"/chat/thread/{thread_id}/transfer-organizer", json=data)

    async def accept_organizer(self, thread_id: str, request_id: str) -> int:
        return await self.request("POST", f"/chat/thread/{thread_id}/transfer-organizer/{request_id}/accept")
        
    async def delete_chat(self, thread_id: str) -> int:
        return await self.request("DELETE", f"/chat/thread/{thread_id}")
    
    async def subscribe(self, uid: str, autoRenew: str = False, transaction_id: str = None) -> int:
        data = jsonify(paymentContext=jsonify(
                transactionId=transaction_id or str(uuid4()),
                isAutoRenew=autoRenew
            )
        )

        return await self.request("POST", f"/influencer/{uid}/subscribe", json=data)

    async def promotion(self, notice_id: str, type: str = "accept") -> int:
        return await self.request("POST", f"/notice/{notice_id}/{type}")
    
    async def play_quiz(self, quiz_id: str, answers: list, quiz_mode: int = 0) -> int:
        quiz_answers = []

        for answer in answers:
            part = jsonify(
                optIdList=[answer[1]],
                quizQuestionId=answer[0],
                timeSpent=answer[2] if len(answer) == 3 else 0.0
            )

            quiz_answers.append(json.loads(part))

        data = jsonify(
            mode=quiz_mode,
            quizAnswerList=quiz_answers
        )

        return await self.request("POST", f"/blog/{quiz_id}/quiz/result", json=data)
    
    async def vc_permission(self, thread_id: str, permission: int) -> int:
        data = jsonify(vvChatJoinType=permission)
        return await self.request("POST", f"/chat/thread/{thread_id}/vvchat-permission", json=data)

    async def get_vc_reputation_info(self, thread_id: str) -> VcReputation:
        response = await self.request("GET", f"/chat/thread/{thread_id}/avchat-reputation")
        return VcReputation(**response)

    async def claim_vc_reputation(self, thread_id: str) -> VcReputation:
        response = await self.request("POST", f"/chat/thread/{thread_id}/avchat-reputation")
        return VcReputation(**response)

    async def get_online_favorite_users(self, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-group/quick-access?type=online&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))

    async def get_user_checkins(self, uid: str) -> List[CheckIn]:
        response = await self.request("GET", f"/check-in/stats/{uid}?timezone={0}")
        return list(map(lambda o: CheckIn(**o), response))

    async def get_user_blogs(self, uid: str, start: int = 0, size: int = 100) -> List[Blog]:
        response = await self.request("GET", f"/blog?type=user&q={uid}&start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))

    async def get_user_wikis(self, uid: str, start: int = 0, size: int = 100) -> List[Wiki]:
        response = await self.request("GET", f"/item?type=user-all&start={start}&size={size}&cv=1.2&uid={uid}")
        return list(map(lambda o: Wiki(**o), response["itemList"]))

    async def get_user_achievements(self, uid: str) -> Achievement:
        response = await self.request("GET", f"/user-profile/{uid}/achievements")
        return Achievement(**response["achievements"])

    async def get_influencer_fans(self, uid: str, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/influencer/{uid}/fans?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response))

    async def search_users(self, nickname: str, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/user-profile?type=name&q={nickname}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))

    async def get_saved_blogs(self, start: int = 0, size: int = 100) -> List[Bookmark]:
        response = await self.request("GET", f"/bookmark?start={start}&size={size}")
        return list(map(lambda o: Bookmark(**o), response["bookmarkList"]))
    
    async def get_leaderboard_info(self, type: int, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/community/leaderboard?rankingType={type}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))

    async def get_blog_tipped_users(self, blog_id: str, start: int = 0, size: int = 100) -> List[TippedUserSummary]:
        response = await self.request("GET", f"/blog/{blog_id}/tipping/tipped-users-summary?start={start}&size={size}")
        return list(map(lambda o: TippedUserSummary(**o), response))

    async def get_wiki_tipped_users(self, wiki_id: str, start: int = 0, size: int = 100) -> List[TippedUserSummary]:
        response = await self.request("GET", f"/item/{wiki_id}/tipping/tipped-users-summary?start={start}&size={size}")
        return list(map(lambda o: TippedUserSummary(**o), response))
    
    async def get_chat_tipped_users(self, thread_id: str, start: int = 0, size: int = 100) -> List[TippedUserSummary]:
        response = await self.request("GET", f"/chat/thread/{thread_id}/tipping/tipped-users-summary?start={start}&size={size}")
        return list(map(lambda o: TippedUserSummary(**o), response))
    
    async def get_file_tipped_users(self, file_id: str, start: int = 0, size: int = 100) -> List[TippedUserSummary]:
        response = await self.request("GET", f"/shared-folder/files/{file_id}/tipping/tipped-users-summary?start={start}&size={size}")
        return list(map(lambda o: TippedUserSummary(**o), response))

    async def get_public_chat_threads(self, type: str = "recommended", start: int = 0, size: int = 100) -> List[Thread]:
        response = await self.request("GET", f"/chat/thread?type=public-all&filterType={type}&start={start}&size={size}")
        return list(map(lambda o: Thread(**o), response["threadList"]))
    
    async def get_blog_categories(self, size: int = 100) -> List[BlogCategory]:
        response = await self.request("GET", f"/blog-category?size={size}")
        return list(map(lambda o: BlogCategory(**o), response["blogCategoryList"]))

    async def get_blogs_by_category(self, category_id: str, start: int = 0, size: int = 100) -> List[Blog]:
        response = await self.request("GET", f"/blog-category/{category_id}/blog-list?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))

    async def get_quiz_rankings(self, quiz_id: str, start: int = 0, size: int = 100)-> QuizRanking:
        response = await self.request("GET", f"/blog/{quiz_id}/quiz/result?start={start}&size={size}")
        return QuizRanking(**response)

    async def get_recent_blogs(self, page_token: str = None, start: int = 0, size: int = 100) -> Blog:
        if not page_token: params = f"v=2&pagingType=t&start={start}&size={size}"
        else: params = f"v=2&pagingType=t&pageToken={page_token}&start={start}&size={size}"
        
        response = await self.request("GET", f"/feed/blog-all?{params}")
        return list(map(lambda o: Message(**o, **response.get("paging", {})),  response["blogList"]))
    
    async def get_recent_wikis(self, start: int = 0, size: int = 25):
        response = await self.request("GET", f"/item?type=catalog-all&start={start}&size={size}")
        return list(map(lambda o: Wiki(**o), response["itemList"]))
    
    async def get_notifications(self, start: int = 0, size: int = 100) -> Dict:
        return await self.request("GET", f"/notification?pagingType=t&start={start}&size={size}")["notificationList"]
    
    async def get_sticker_pack_info(self, sticker_pack_id: str) -> StickerCollection:
        response = await self.request("GET", f"/sticker-collection/{sticker_pack_id}?includeStickers=true")
        return StickerCollection(**response["stickerCollection"])

    async def get_sticker_packs(self) -> List[StickerCollection]:
        response = await self.request("GET", f"/sticker-collection?includeStickers=false&type=my-active-collection")
        return list(map(lambda o: StickerCollection(**o), response["stickerCollection"]))

    async def get_store_chat_bubbles(self, start: int = 0, size: int = 100) -> List[StoreItem]:
        response = await self.request("GET", f"/store/items?sectionGroupId=chat-bubble&start={start}&size={size}")
        return list(map(lambda o: StoreItem(**o), response["stickerCollection"]))

    async def get_store_stickers(self, start: int = 0, size: int = 100) -> List[StoreItem]:
        response = await self.request("GET", f"/store/items?sectionGroupId=sticker&start={start}&size={size}")
        return list(map(lambda o: StoreItem(**o), response["stickerCollection"]))
    
    async def get_community_stickers(self) -> List[StickerCollection]:
        response = await self.request("GET", f"/sticker-collection?type=community-shared")
        return list(map(lambda o: StickerCollection(**o), response))

    async def get_sticker_collection(self, collection_id: str) -> StickerCollection:
        response = await self.request("GET", f"/sticker-collection/{collection_id}?includeStickers=true")
        return StickerCollection(**response["stickerCollection"])

    async def get_shared_folder_info(self) -> Dict:
        return await self.request("GET", f"/shared-folder/stats")["stats"]

    async def get_shared_folder_files(self, type: str = "latest", start: int = 0, size: int = 100) -> Dict:
        return await self.request("GET", f"/shared-folder/files?type={type}&start={start}&size={size}")["fileList"]

    async def get_hidden_blogs(self, start: int = 0, size: int = 100) -> Blog:
        response = await self.request("GET", f"/feed/blog-disabled?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))

    async def review_quiz_questions(self, quiz_id: str) -> List[Blog.QuizQuestion]:
        response = await self.request("GET", f"/blog/{quiz_id}?action=review")
        return list(map(lambda o: Blog.QuizQuestion(**o), response["blog"]["quizQuestionList"]))

    async def get_recent_quiz(self, start: int = 0, size: int = 100) -> Blog:
        response = await self.request("GET", f"/blog?type=quizzes-recent&start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))

    async def get_trending_quiz(self, start: int = 0, size: int = 100) -> Blog:
        response = await self.request("GET", f"/feed/quiz-trending?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))

    async def get_best_quiz(self, start: int = 0, size: int = 100) -> Blog:
        response = await self.request("GET", f"/feed/quiz-best-quizzes?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))

    async def reorder_featured_users(self, uids: list) -> int:
        data = jsonify(uidList=uids)
        return await self.request("POST", f"/user-profile/featured/reorder", json=data)
    
    async def user_moderation_history(self, uid: str = None, size: int = 100) -> List[AdminLog]:
        response = await self.request("GET", f"/admin/operation?pagingType=t&size={size}&objectId={uid}&objectType={ObjectTypes.USER}")
        return list(map(lambda o: AdminLog(**o), response["adminLogList"]))

    async def blog_moderation_history(self, blog_id: str = None, size: int = 100) -> List[AdminLog]:
        response = await self.request("GET", f"/admin/operation?pagingType=t&size={size}&objectId={blog_id}&objectType={ObjectTypes.BLOG}")
        return list(map(lambda o: AdminLog(**o), response["adminLogList"]))

    async def wiki_moderation_history(self, wiki_id: str = None, size: int = 100) -> List[AdminLog]:
        response = await self.request("GET", f"/admin/operation?pagingType=t&size={size}&objectId={wiki_id}&objectType={ObjectTypes.ITEM}")
        return list(map(lambda o: AdminLog(**o), response["adminLogList"]))

    async def file_moderation_history(self, file_id: str = None, size: int = 100) -> List[AdminLog]:
        response = await self.request("GET", f"/admin/operation?pagingType=t&size={size}&objectId={file_id}&objectType={ObjectTypes.FOLDER_FILE}")
        return list(map(lambda o: AdminLog(**o), response["adminLogList"]))

    async def feature_user(self, seconds: int, uid: str) -> int:
        data = jsonify(
            adminOpName=114, 
            adminOpValue=jsonify(
                featuredDuration=seconds, 
                featuredType=FeaturedTypes.USER
            )
        )

        return await self.request("POST", f"/user-profile/{uid}/admin", json=data)

    async def feature_blog(self, seconds: int, blog_id: str) -> int:
        data = jsonify(
            adminOpName=114, 
            adminOpValue=jsonify(
                featuredDuration=seconds, 
                featuredType=FeaturedTypes.BLOG
            )
        )

        return await self.request("POST", f"/blog/{blog_id}/admin", json=data)

    async def feature_wiki(self, seconds: int, wiki_id: str) -> int:
        data = jsonify(
            adminOpName=114, 
            adminOpValue=jsonify(
                featuredDuration=seconds, 
                featuredType=FeaturedTypes.WIKI
            )
        )

        return await self.request("POST", f"/item/{wiki_id}/admin", json=data)

    async def feature_chat(self, seconds: int, thread_id: str) -> int:
        data = jsonify(
            adminOpName=114,
            adminOpValue=jsonify(
                featuredDuration=seconds,
                featuredType=FeaturedTypes.CHAT
            )
        )

        return await self.request("POST", f"/chat/thread/{thread_id}/admin", json=data)

    async def unfeature_user(self, uid: str) -> int:
        data = jsonify(
            adminOpName=114,
            adminOpValue=jsonify(
                featuredType=FeaturedTypes.UNFEATURE
            )
        )

        return await self.request("POST", f"/user-profile/{uid}/admin", json=data)

    async def unfeature_blog(self, blog_id: str) -> int:
        data = jsonify(
            adminOpName=114,
            adminOpValue=jsonify(
                featuredType=FeaturedTypes.UNFEATURE
            )
        )

        return await self.request("POST", f"/blog/{blog_id}/admin", json=data)

    async def unfeature_wiki(self, wiki_id: str) -> int:
        data = jsonify(
            adminOpName=114,
            adminOpValue=jsonify(
                featuredType=FeaturedTypes.UNFEATURE
            )
        )

        return await self.request("POST", f"/item/{wiki_id}/admin", json=data)

    async def unfeature_chat(self, thread_id: str) -> int:
        data = jsonify(
            adminOpName=114,
            adminOpValue=jsonify(
                featuredType=FeaturedTypes.UNFEATURE
            )
        )

        return await self.request("POST", f"/chat/thread/{thread_id}/admin", json=data)
    
    async def hide_user(self, uid: str, reason: str = None) -> int:
        data = jsonify(
            adminOpName=18,
            adminOpValue=9,
            adminOpNote=jsonify(content=reason)
        )

        return await self.request("POST", f"/user-profile/{uid}/admin", json=data)

    async def hide_blog(self, blog_id: str, reason: str = None) -> int:
        data = jsonify(
            adminOpName=110,
            adminOpValue=9,
            adminOpNote=jsonify(content=reason)
        )

        return await self.request("POST", f"/blog/{blog_id}/admin", json=data)

    async def hide_wiki(self, wiki_id: str, reason: str = None) -> int:
        data = jsonify(
            adminOpName=110,
            adminOpValue=9,
            adminOpNote=jsonify(content=reason)
        )

        return await self.request("POST", f"/item/{wiki_id}/admin", json=data)

    async def hide_chat(self, thread_id: str, reason: str = None) -> int:
        data = jsonify(
            adminOpName=110,
            adminOpValue=9,
            adminOpNote=jsonify(content=reason)
        )

        return await self.request("POST", f"/chat/thread/{thread_id}/admin", json=data)

    async def unhide_user(self, uid: str, reason: str = None) -> int:
        data = jsonify(
            adminOpName=19,
            adminOpValue=0,
            adminOpNote=jsonify(content=reason)
        )

        return await self.request("POST", f"/user-profile/{uid}/admin", json=data)

    async def unhide_blog(self, blog_id: str, reason: str = None) -> int:
        data = jsonify(
            adminOpName=110,
            adminOpValue=0,
            adminOpNote=jsonify(content=reason)
        )

        return await self.request("POST", f"/blog/{blog_id}/admin", json=data)

    async def unhide_wiki(self, wiki_id: str, reason: str = None) -> int:
        data = jsonify(
            adminOpName=110,
            adminOpValue=0,
            adminOpNote=jsonify(content=reason)
        )

        return await self.request("POST", f"/item/{wiki_id}/admin", json=data)

    async def unhide_chat(self, thread_id: str, reason: str = None) -> int:
        data = jsonify(
            adminOpName=110,
            adminOpValue=0,
            adminOpNote=jsonify(content=reason)
        )

        return await self.request("POST", f"/chat/thread/{thread_id}/admin", json=data)

    async def edit_titles(self, uid: str, titles: list) -> int:
        data = jsonify(
            adminOpName=207,
            adminOpValue=jsonify(
                titles=titles
            )
        )

        return await self.request("POST", f"/user-profile/{uid}/admin", json=data)
    
    async def warn(self, uid: str, reason: str = None) -> int:
        data = jsonify(
            uid=uid,
            title="Custom",
            content=reason,
            attachedObject=jsonify(
                objectId=uid,
                objectType=ObjectTypes.USER
            ),
            penaltyType=0,
            adminOpNote={},
            noticeType=7
        )

        return await self.request("POST", f"/notice", json=data)

    async def strike(self, uid: str, seconds: int, title: str = None, reason: str = None) -> int:
        data = jsonify(
            uid=uid,
            title=title,
            content=reason,
            attachedObject=jsonify(
                objectId=uid,
                objectType=ObjectTypes.USER
            ),
            penaltyType=1,
            adminOpNote={},
            penaltyValue=seconds,
            noticeType=4
        )

        return await self.request("POST", f"/notice", json=data)
    
    async def ban(self, uid: str, reason: str, reason_type: int = None) -> int:
        data = jsonify(reasonType=reason_type, note=jsonify(content=reason))
        return await self.request("POST", f"/user-profile/{uid}/ban", json=data)

    async def unban(self, uid: str, reason: str = None) -> int:
        data = jsonify(note=jsonify(content=reason))
        return await self.request("POST", f"/user-profile/{uid}/unban", json=data)
    
    async def purchase(self, object_id: str, object_type: int, autoRenew: bool = False) -> int:
        data = jsonify(
            v=1,
            objectId=object_id,
            objectType=object_type,
            paymentContext=jsonify(
                discountStatus=1, 
                discountValue=1, 
                isAutoRenew=autoRenew
            )
        )

        if self.auth.user.membershipStatus == 0:
            data["paymentContext"]["discountStatus"] = 0

        return await self.request("POST", f"/store/purchase", json=data)

    async def add_poll_option(self, blog_id: str, question: str) -> int:
        data = jsonify(mediaList=None, title=question, type=0)
        return await self.request("POST", f"/blog/{blog_id}/poll/option", json=data)

    async def create_wiki_category(self, title: str, parent_category_id: str, content: str = None) -> int:
        data = jsonify(
            content=content,
            icon=None,
            label=title,
            mediaList=None,
            parentCategoryId=parent_category_id
        )

        return await self.request("POST", f"/item-category", json=data)

    async def create_shared_folder(self, title: str) -> int:
        data = jsonify(title=title)
        return await self.request("POST", f"/shared-folder/folders", json=data)

    async def submit_to_wiki(self, wiki_id: str, message: str) -> int:
        data = jsonify(message=message, itemId=wiki_id)
        return await self.request("POST", f"/knowledge-base-request", json=data)

    async def accept_wiki_request(self, request_id: str, destination_category_id_list: list) -> int:
        data = jsonify(destinationCategoryIdList=destination_category_id_list, actionType="create")
        return await self.request("POST", f"/knowledge-base-request/{request_id}/approve", json=data)

    async def reject_wiki_request(self, request_id: str) -> int:
        return await self.request("POST", f"/knowledge-base-request/{request_id}/reject")

    async def get_wiki_submissions(self, start: int = 0, size: int = 100) -> Dict:
        return (await self.request("GET", f"/knowledge-base-request?type=all&start={start}&size={size}"))["knowledgeBaseRequestList"]
    
    # Live Layer (i dont finish this)
    async def get_live_layer(self) -> Dict:
        return (await self.request("GET", f"/live-layer/homepage?v=2"))["liveLayerList"]
    
    async def get_online_users(self, ndc_id: int = None, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:online-members&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_online_users_count(self, ndc_id: int = None) -> int:
        return (await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:online-members&start=0&size=1"))["userProfileCount"]
    
    async def get_public_chats(self, start: int = 0, size: int = 100) -> List[Thread]:
        response = await self.request("GET", f"/live-layer/public-chats?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["threadList"]))
    
    async def get_chatting_users(self, ndc_id: int = None, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-chatting&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_chatting_users_count(self, ndc_id: int = None) -> int:
        return (await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-chatting&start=0&size=1"))["userProfileCount"]

    async def get_live_chats(self, start: int = 0, size: int = 100) -> List[Thread]:
        response = await self.request("GET", f"/live-layer/public-live-chats?start={start}&size={size}")
        return list(map(lambda o: Thread(**o), response["threadList"]))
    
    async def get_live_chatting_users(self, ndc_id: int = None, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-live-chatting&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_live_chatting_users_count(self, ndc_id: int = None) -> int:
        return (await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-live-chatting&start=0&size=1"))["userProfileCount"]

    async def get_playing_quizzes(self, start: int = 0, size: int = 100) -> List[Blog]:
        response = await self.request("GET", f"/live-layer/quizzes?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))
    
    async def get_playing_quizzes_users(self, ndc_id: int = None, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-playing-quizzes&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_playing_quizzes_users_count(self, ndc_id: int = None) -> int:
        return (await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-playing-quizzes&start=0&size=1"))["userProfileCount"]

    async def get_browsing_blogs(self, start: int = 0, size: int = 100) -> List[Blog]:
        response = await self.request("GET", f"/live-layer/blogs?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response["blogList"]))
    
    async def get_browsing_blogs_users(self, ndc_id: int = None, start: int = 0, size: int = 100) -> List[UserProfile]:
        response = await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-browsing-blogs&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def get_browsing_blogs_users_count(self, ndc_id: int = None) -> int:
        return (await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-browsing-blogs&start=0&size=1"))["userProfileCount"]

    async def get_blog_users(self, blog_id: str, ndc_id: int = None, start: int = 0, size: int = 100):
        response = await self.request("GET", f"/live-layer?topic=ndtopic:x{ndc_id or self.ndc_id}:users-browsing-blog-at:{blog_id}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))
    
    async def activate_bubble(self, bubble_id: str) -> int:
        return await self.request("POST", f"/chat/chat-bubble/{bubble_id}/activate")

    async def deactivate_bubble(self, bubble_id: str) -> int:
        return await self.request("POST", f"/chat/chat-bubble/{bubble_id}/deactivate")

    async def send_active_object(self, timers: List[Dict], timezone: int = 0, flags: int = 2147483647):
        data = jsonify(userActiveTimeChunkList=timers, optInAdsFlags=flags, timezone=timezone, timestamp=int(time() * 1000))
        return await self.request("POST", "/community/stats/user-active-time", data=json_minify(json.dumps(data)))
    
    async def create_community(self, name: str, tagline: str, icon: Union[str, bytes], themeColor: str, joinType: int = 0, primaryLanguage: str = "en"):
        data = jsonify(
            icon=jsonify(
                height=512.0,
                imageMatrix=[1.6875, 0.0, 108.0, 0.0, 1.6875, 497.0, 0.0, 0.0, 1.0],
                path=await self.upload_media(icon) if isinstance(bytes) else icon,
                width=512.0,
                x=0.0,
                y=0.0
            ),
            joinType=joinType,
            name=name,
            primaryLanguage=primaryLanguage,
            tagline=tagline,
            templateId=9,
            themeColor=themeColor
        )

        response = await self.request("POST", f"/community", json=data, ndc_id=GLOBAL_ID)
        return response

    async def delete_community(
        self, 
        email: str, 
        password: str, 
        code: str, 
        ndc_id: int = None
    ):
        data = jsonify(
            secret=f"0 {password}",
            validationContext=jsonify(
                data=jsonify(
                    code=code
                ),
                type=1,
                identity=email
            ),
            deviceID=self.device_id
        )

        response = await self.request("POST", f"/community/delete-request", json=data,  ndc_id=-(ndc_id or self.ndc_id))
        return response

    async def get_managed_communities(self, start: int = 0, size: int = 25):
        response = await self.request("GET", f"/community/managed?start={start}&size={size}", ndc_id=GLOBAL_ID)
        return list(map(lambda o: Community(**o), response["communityList"]))
    
    # TODO : Finish it
    async def get_categories(self, start: int = 0, size: int = 25):
        response = await self.request("GET", f"/blog-category?start={start}&size={size}")
        return response

    async def change_sidepanel_color(self, color: str):
        data = jsonify(
            path=PathTypes.LEFT_SIDE_PANEL_ICON_COLOR,
            value=color
        )

        response = await self.request("POST", f"/community/configuration", json=data)
        return response

    async def upload_themepack_raw(self, file: bytes):
        response = await self.request("POST", f"/media/upload/target/community-theme-pack", data=file)
        return response

    async def promote(self, userId: str, rank: str):
        data = jsonify()

        response = await self.request("POST", f"/user-profile/{userId}/{rank}", json=data)
        return response

    async def get_join_requests(self, start: int = 0, size: int = 25):
        response = await self.request("GET", f"/community/membership-request?status=pending&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["communityMembershipRequestList"])) 
    
    async def get_join_requests(self, start: int = 0, size: int = 25):
        response = await self.request("GET", f"/community/membership-request?status=pending&start={start}&size={size}")
        return response["communityMembershipRequestCount"]

    async def accept_join_request(self, userId: str):
        response = await self.request("POST", f"/community/membership-request/{userId}/accept", json={})
        return response

    async def reject_join_request(self, userId: str):
        response = await self.request("POST", f"/community/membership-request/{userId}/reject", json={})
        return response

    async def get_community_stats(self):
        response = await self.request("GET", f"/community/stats")
        return CommunityStatistic(**response['communityStats'])

    async def get_community_user_stats(self, type: str, start: int = 0, size: int = 25):
        response = await self.request("GET", f"/community/stats/moderation?type={type}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response["userProfileList"]))

    async def change_welcome_message(self, message: str, isEnabled: bool = True):
        data = jsonify(
            path=PathTypes.WELCOME_MESSAGE,
            value=jsonify(
                enabled=isEnabled,
                text=message
            )
        )

        response = await self.request("POST", f"/community/configuration", json=data)
        return response

    async def change_guidelines(self, message: str):
        data = jsonify(content=message)

        response = await self.request("POST", f"/community/guideline", json=data)
        return response

    async def edit_community(
        self, 
        name: str = None, 
        content: str = None, 
        aminoId: str = None, 
        primaryLanguage: str = None, 
        themePackUrl: str = None,
        join_type: int = None # 0 - open, 1 - reqest, 2 - close
    ):
        data = jsonify(
            name=name,
            content=content,
            endpoint=aminoId,
            primaryLanguage=primaryLanguage,
            themePackUrl=themePackUrl,
            joinType=join_type
        )

        response = await self.request("POST", f"/community/settings", json=data)
        return response

    async def change_module(self, module: str, isEnabled: bool):
        data = jsonify(path=module, value=isEnabled)

        response = await self.request("POST", f"/community/configuration", json=data)
        return response

    async def add_influencer(self, userId: str, monthlyFee: int):
        data = jsonify(monthlyFee=monthlyFee)

        response = await self.request("POST", f"/influencer/{userId}", json=data)
        return response

    async def remove_influencer(self, userId: str):
        response = await self.request("DELETE", f"/influencer/{userId}")
        return response
    
    # TODO : Finish it
    async def get_notice_list(self, start: int = 0, size: int = 25, type: str = "management"):
        response = await self.request("GET", f"/notice?type={type}&status=1&start={start}&size={size}")
        return response["noticeList"]

    async def delete_pending_role(self, noticeId: str):
        response = self.request("DELETE", f"/notice/{noticeId}")
        return response

from asyncio import get_event_loop, new_event_loop
from asyncio.events import AbstractEventLoop
from base64 import b64encode
from time import time, timezone
from typing import BinaryIO, Union, List
from uuid import uuid4
from aiohttp import ClientSession, ClientTimeout
from json_minify import json_minify
from ujson import dumps, loads

from .utils.models import *
from .utils.types import *
from .utils.helpers import *
from .utils.exceptions import *
from .http_client import AminoHttpClient


class CommunityClient(AminoHttpClient):
    def __init__(self, comId: int,
        loop: Optional[AbstractEventLoop] = None,
        session: Optional[ClientSession] = None, 
        info: Optional[Community] = None,
        settings: Optional[dict] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[str] = None
    ) -> None:
        self._session: ClientSession = session or ClientSession(
            timeout=ClientTimeout(60), json_serialize=dumps)
        self._loop: AbstractEventLoop = loop or get_event_loop()
        
        self.comId = comId
        self.headers = settings or self.headers

        self.proxy: Optional[str] = proxy
        self.proxy_auth: Optional[str] = proxy_auth
        
        self.profile: UserProfile = UserProfile(**{})
        self.info: Community = info or Community(**{})

    async def __aenter__(self) -> "CommunityClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self._session.close()
    
    def __del__(self):
        self._loop.create_task(self._close_session())
    
    @property
    def event_loop(self):
        if not self._loop:
            try:
                self._loop = get_event_loop()
            except RuntimeError:
                self._loop = new_event_loop()
        return self._loop

    async def _close_session(self):
        if not self.session.closed:
            await self.session.close()
    
    async def get_invite_codes(self, status: str = "normal", start: int = 0, size: int = 25) -> List[InviteCode]:
        response = await self.get(f"/g/s-x{self.comId}/community/invitation?status={status}&start={start}&size={size}")
        return list(map(lambda o: InviteCode(**o), (await response.json())["communityInvitationList"]))

    async def get_user_info(self, userId: str) -> UserProfile:
        response = await self.get(f"/x{self.comId}/s/user-profile/{userId}")
        return UserProfile(**(await response.json())["userProfile"])

    async def generate_invite_code(self, duration: int = 0, force: bool = True):
        data = {
            "duration": duration,
            "force": force,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/g/s-x{self.comId}/community/invitation", data)
        return InviteCode(**(await response.json())["communityInvitation"])

    async def delete_invite_code(self, inviteId: str) -> int:
        response = await self.delete(f"/g/s-x{self.comId}/community/invitation/{inviteId}")
        return response.status
    
    async def delete_blog(self, blogId: str) -> int:
        response = await self.delete(f"/x{self.comId}/s/blog/{blogId}")
        return response.status

    async def delete_wiki(self, wikiId: str) -> int:
        response = await self.delete(f"/x{self.comId}/s/item/{wikiId}")
        return response.status
    
    async def upload_media(self, file: BinaryIO, fileType: str) -> str:
        response = await self.post(f"/x{self.comId}/s/media/upload", data=file.read(), type=fileType)
        return (await response.json())["mediaValue"]

    async def post_blog(self, title: str, content: str, imageList: list = None, captionList: list = None, 
            categoriesList: list = None, backgroundColor: str = None, fansOnly: bool = False, extensions: dict = None) -> int:
        if captionList and imageList:
            mediaList = [[100, self.upload_media(image, "image"), caption] for image, caption in zip(imageList, captionList)]

        elif imageList:
            mediaList = [[100, self.upload_media(image, "image"), None] for image in imageList]

        data = {
            "address": None,
            "content": content,
            "title": title,
            "mediaList": mediaList,
            "extensions": extensions,
            "latitude": 0,
            "longitude": 0,
            "eventSource": SourceTypes.GLOBAL_COMPOSE,
            "timestamp": int(time() * 1000)
        }

        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if categoriesList: data["taggedBlogCategoryIdList"] = categoriesList

        response = await self.post(f"/x{self.comId}/s/blog", data)
        return response.status
    
    async def post_wiki(self, title: str, content: str, icon: str = None, imageList: list = None,
            keywords: str = None, backgroundColor: str = None, fansOnly: bool = False) -> int:

        mediaList = [[100, self.upload_media(image, "image"), None] for image in imageList]

        data = {
            "label": title,
            "content": content,
            "mediaList": mediaList,
            "eventSource": SourceTypes.GLOBAL_COMPOSE,
            "timestamp": int(time() * 1000)
        }

        if icon: data["icon"] = icon
        if keywords: data["keywords"] = keywords
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}

        response = await self.post(f"/x{self.comId}/s/item", data)
        return response.status

    async def edit_blog(self, blogId: str, title: str = None, content: str = None, imageList: list = None, 
            categoriesList: list = None, backgroundColor: str = None, fansOnly: bool = False) -> int:
        mediaList = [[100, self.upload_media(image, "image"), None] for image in imageList]

        data = {
            "address": None,
            "mediaList": mediaList,
            "latitude": 0,
            "longitude": 0,
            "eventSource": "PostDetailView",
            "timestamp": int(time() * 1000)
        }

        if title: data["title"] = title
        if content: data["content"] = content
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if categoriesList: data["taggedBlogCategoryIdList"] = categoriesList

        response = await self.post(f"/x{self.comId}/s/blog/{blogId}", data)
        return response.status
    
    async def repost_blog(self, content: str = None, blogId: str = None, wikiId: str = None) -> int:
        if blogId:
            refObjectId, refObjectType = blogId, ObjectTypes.BLOG
        elif wikiId: 
            refObjectId, refObjectType = wikiId, ObjectTypes.ITEM
        else: raise SpecifyType()

        data = {
            "content": content,
            "refObjectId": refObjectId,
            "refObjectType": refObjectType,
            "type": 2,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/blog", data)
        return response.status
    
    async def check_in(self, tz: int = -timezone // 1000) -> CheckIn:
        data = {
            "timezone": tz,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/check-in", data)
        return CheckIn(**(await response.json()))

    async def repair_check_in(self, method: int = RepairTypes.COINS) -> int:
        data = {
            "repairMethod": method,
            "timestamp": int(time() * 1000)
        }
        response = await self.post(f"/x{self.comId}/s/check-in/repair", data)
        return response.status

    async def lottery(self, tz: int = -timezone // 1000) -> int:
        data = {
            "timezone": tz,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/check-in/lottery", data)
        return Lottery(**(await response.json())["lotteryLog"])
    
    async def edit_profile(self, nickname: str = None, content: str = None, icon: BinaryIO = None, chatRequestPrivilege: str = None, 
            imageList: list = None, captionList: list = None, backgroundImage: str = None, backgroundColor: str = None, 
            titles: list = None, colors: list = None, defaultBubbleId: str = None) -> int:
        data = {"timestamp": int(time() * 1000)}

        if captionList and imageList:
            mediaList = [[100, self.upload_media(image, "image"), caption] for image, caption in zip(imageList, captionList)]

        elif imageList:
            mediaList = [[100, self.upload_media(image, "image"), None] for image in imageList]

        if imageList or captionList and imageList:
            data["mediaList"] = mediaList

        if nickname: data["nickname"] = nickname
        if icon: data["icon"] = self.upload_media(icon, "image")
        if content: data["content"] = content

        if chatRequestPrivilege: data["extensions"] = {"privilegeOfChatInviteRequest": chatRequestPrivilege}
        if backgroundImage: data["extensions"] = {"style": {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if defaultBubbleId: data["extensions"] = {"defaultBubbleId": defaultBubbleId}

        if titles or colors:
            tlt = [{"title": titles, "color": colors} for titles, colors in zip(titles, colors)]
            data["extensions"] = {"customTitles": tlt}

        response = await self.post(f"/x{self.comId}/s/user-profile/{self.userId}", data)
        return response.status
    
    async def vote_poll(self, blogId: str, optionId: str) -> int:
        data = {
            "value": 1,
            "eventSource": SourceTypes.DATAIL_POST,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/blog/{blogId}/poll/option/{optionId}/vote", data)
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
            response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/g-comment", data)
            return response.status

        elif blogId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/x{self.comId}/s/blog/{blogId}/g-comment", data)
            return response.status

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/x{self.comId}/s/item/{wikiId}/g-comment", data)
            return response.status

        else: raise SpecifyType()
    
    async def delete_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
        if userId: url = f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}"
        elif blogId: url = f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}"
        elif wikiId: url = f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}"
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
                response = await self.post(f"/x{self.comId}/s/blog/{blogId}/g-vote?cv=1.2", data)
                return response.status

            elif isinstance(blogId, list):
                data["targetIdList"] = blogId
                response = await self.post(f"/x{self.comId}/s/feed/g-vote", data)
                return response.status

            else: raise WrongType(type(blogId))

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/x{self.comId}/s/item/{wikiId}/g-vote?cv=1.2", data)
            return response.status

        else: raise SpecifyType()

    async def unlike_blog(self, blogId: str = None, wikiId: str = None) -> int:
        if blogId:
            url = f"/x{self.comId}/s/blog/{blogId}/vote?eventSource=UserProfileView"

        elif wikiId:
            url = f"/x{self.comId}/s/item/{wikiId}/vote?eventSource=PostDetailView"

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
            response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
            return response.status

        elif blogId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
            return response.status

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = await self.post(f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
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
    
    async def upvote_comment(self, blogId: str, commentId: str) -> int:
        data = {
            "value": 1,
            "eventSource": "PostDetailView",
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1", data)
        return response.status

    async def downvote_comment(self, blogId: str, commentId: str) -> int:
        data = {
            "value": -1,
            "eventSource": "PostDetailView",
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=-1", data)
        return response.status

    async def unvote_comment(self, blogId: str, commentId: str) -> int:
        response = await self.delete(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?eventSource=PostDetailView")
        return response.status
    
    async def reply_wall(self, userId: str, commentId: str, message: str) -> int:
        data = {
            "content": message,
            "stackedId": None,
            "respondTo": commentId,
            "type": 0,
            "eventSource": "UserProfileView",
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/comment", data)
        return response.status

    async def activity_status(self, status: int) -> int:
        data = {
            "onlineStatus": status,
            "duration": 86400,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/user-profile/{self.userId}/online-status", data)
        return response.status
    
    async def check_notifications(self) -> int:
        response = await self.post(f"/x{self.comId}/s/notification/checked")
        return response.status

    async def delete_notification(self, notificationId: str) -> int:
        response = await self.delete(f"/x{self.comId}/s/notification/{notificationId}")
        return response.status

    async def clear_notifications(self) -> int:
        response = await self.delete(f"/x{self.comId}/s/notification")
        return response.status
    
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

        response = await self.post(f"/x{self.comId}/s/chat/thread", data)
        return Thread(**(await response.json()))
    
    async def invite_to_chat(self, userId: Union[str, list], chatId: str) -> int:
        data = {
            "uids": userId if isinstance(userId, list) else [userId],
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/invite", data)
        return response.status

    async def add_to_favorites(self, userId: str) -> int:
        response = await self.post(f"/x{self.comId}/s/user-group/quick-access/{userId}")
        return response.status
    
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
            response = await self.post(f"/x{self.comId}/s/blog/{blogId}/tipping", data)
            return response.status
        
        elif chatId:
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping", data)
            return response.status
        
        elif objectId:
            data["objectId"] = objectId
            data["objectType"] = ObjectTypes.ITEM
            response = await self.post(f"/x{self.comId}/s/tipping", data)
            return response.status
        
        else: SpecifyType() 

    async def thank_tip(self, chatId: str, userId: str) -> int:
        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping/tipped-users/{userId}/thank")
        return response.status
    
    async def follow(self, userId: Union[str, list]) -> int:
        if isinstance(userId, str):
            response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/member")
            return response.status

        elif isinstance(userId, list):
            data = {"targetUidList": userId, "timestamp": int(time() * 1000)}
            response = await self.post(f"/x{self.comId}/s/user-profile/{self.userId}/joined", data)
            return response.status

        else: raise WrongType(type(userId))

    async def unfollow(self, userId: str) -> int:
        response = await self.delete(f"/x{self.comId}/s/user-profile/{self.userId}/joined/{userId}")
        return response.status
    
    async def block(self, userId: str) -> int:
        response = await self.post(f"/x{self.comId}/s/block/{userId}")
        return response.status

    async def unblock(self, userId: str) -> int:
        response = await self.delete(f"/x{self.comId}/s/block/{userId}")
        return response.status
    
    async def flag(self, reason: str, flagType: int, userId: str = None,
            blogId: str = None, wikiId: str = None) -> int:
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

        else: raise SpecifyType

        response = await self.post(f"/x{self.comId}/s/flag", data)
        return response.status
    
    async def send_message(self, chatId: str, message: str = None, type: int = 0, replyTo: str = None, 
            mentions: list = None, embedId: str = None, embedType: int = None, embedLink: str = None, 
            embedTitle: str = None, embedContent: str = None, embedImage: Union[BinaryIO, str] = None) -> Message:

        message = message.replace("<$", "‎‏")
        message = message.replace("$>", "‬‭")
        mentions = [{"uid": uid} for uid in mentions if mentions] if mentions else None

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

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
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
        data["mediaUploadValue"] = b64encode(file.read()).decode()

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Message(**(await response.json())["message"])
    
    async def send_audio(self, chatId: str, file: BinaryIO) -> Message:
        data = {
            "type": 2,
            "mediaType": 110,
            "clientRefId": int(time() / 10 % 1000000000),
            "timestamp": int(time() * 1000)
        }

        data["mediaUploadValueContentType"] = FileTypes.AUDIO
        data["mediaUploadValue"] = b64encode(file.read()).decode()

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Message(**(await response.json())["message"])
    
    async def send_sticker(self, chatId: str, stickerId: str) -> Message:
        data = {
            "type": 3,
            "stickerId": stickerId,
            "clientRefId": int(time() / 10 % 1000000000),
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Message(**(await response.json())["message"])
    
    async def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: str = None) -> int:
        data = {
            "adminOpName": 102,
            "adminOpNote": {"content": reason},
            "timestamp": int(time() * 1000)
        }

        if asStaff and reason:
            data["adminOpNote"] = {"content": reason}

        if not asStaff:
            response = await self.delete(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}")
            return response.status

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}/admin", data)
        return response.status
    
    async def mark_as_read(self, chatId: str, messageId: str):
        data = {
            "messageId": messageId,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/mark-as-read", data)
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
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/co-host", data)
            responses.append(response.status)

        if doNotDisturb is True:
            data = {"alertOption": 2, "timestamp": int(time() * 1000)}
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}/alert", data)
            responses.append(response.status)

        if doNotDisturb is False:
            data = {"alertOption": 1, "timestamp": int(time() * 1000)}
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}/alert", data)
            responses.append(response.status)

        if backgroundImage:
            data = {"media": [100, await self.upload_media(backgroundImage, "image"), None], "timestamp": int(time() * 1000)}
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}/background", data)
            responses.append(response.status)
        
        if pinChat is True: responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/pin", data)).status)
        if pinChat is False: responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/unpin", data)).status)

        if viewOnly is True: responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/enable", data)).status)
        if viewOnly is False: responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/disable", data)).status)

        if canInvite is True: responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/enable", data)).status)
        if canInvite is False: responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/disable", data)).status)

        if canTip is True: responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/enable", data)).status)
        if canTip is False: responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/disable", data)).status)

        responses.append((await self.post(f"/x{self.comId}/s/chat/thread/{chatId}", data)).status)
        return int(sum(responses) / len(responses))
    
    async def transfer_organizer(self, chatId: str, userIds: list) -> int:
        data = {
            "uidList": userIds,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer", data)
        return response.status

    async def accept_organizer(self, chatId: str, requestId: str) -> int:
        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept")
        return response.status

    async def kick(self, userId: str, chatId: str, allowRejoin: bool = True) -> int:
        if allowRejoin: allowRejoin = 1
        if not allowRejoin: allowRejoin = 0

        response = await self.delete(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}?allowRejoin={allowRejoin}")
        return response.status

    async def join_chat(self, chatId: str) -> int:
        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}")
        return response.status

    async def leave_chat(self, chatId: str) -> int:
        response = await self.delete(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}")
        return response.status
        
    async def delete_chat(self, chatId: str) -> int:
        response = await self.delete(f"/x{self.comId}/s/chat/thread/{chatId}")
        return response.status
    
    async def subscribe(self, userId: str, autoRenew: str = False, transactionId: str = None) -> int:
        data = {
            "paymentContext": {
                "transactionId": transactionId or str(uuid4()),
                "isAutoRenew": autoRenew
            },
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/influencer/{userId}/subscribe", data)
        return response.status

    async def promotion(self, noticeId: str, type: str = "accept") -> int:
        response = await self.post(f"/x{self.comId}/s/notice/{noticeId}/{type}")
        return response.status

    async def play_quiz_raw(self, quizId: str, quizAnswerList: list, quizMode: int = 0) -> int:
        data = {
            "mode": quizMode,
            "quizAnswerList": quizAnswerList,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/blog/{quizId}/quiz/result", data)
        return response.status
    
    async def play_quiz(self, quizId: str, questionIdsList: list, answerIdsList: list, quizMode: int = 0) -> int:
        quizAnswerList = []

        for question, answer in zip(questionIdsList, answerIdsList):
            part = {
                "optIdList": [answer],
                "quizQuestionId": question,
                "timeSpent": 0.0
            }

            quizAnswerList.append(loads(part))

        data = {
            "mode": quizMode,
            "quizAnswerList": quizAnswerList,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/blog/{quizId}/quiz/result", data)
        return response.status
    
    async def vc_permission(self, chatId: str, permission: int) -> int:
        data = {
            "vvChatJoinType": permission,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/vvchat-permission", data)
        return response.status

    async def get_vc_reputation_info(self, chatId: str) -> VcReputation:
        response = await self.get(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation")
        return VcReputation(**(await response.json()))

    async def claim_vc_reputation(self, chatId: str) -> VcReputation:
        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation")
        return VcReputation(**(await response.json()))
    
    async def get_all_users(self, type: str = "recent", start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/user-profile?type={type}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))

    async def get_online_favorite_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/user-group/quick-access?type=online&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))

    async def get_user_following(self, userId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/user-profile/{userId}/joined?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))

    async def get_user_followers(self, userId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/user-profile/{userId}/member?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))

    async def get_user_checkins(self, userId: str) -> List[CheckIn]:
        response = await self.get(f"/x{self.comId}/s/check-in/stats/{userId}?timezone={-timezone // 1000}")
        return list(map(lambda o: CheckIn(**o), (await response.json())))

    async def get_user_blogs(self, userId: str, start: int = 0, size: int = 25) -> List[Blog]:
        response = await self.get(f"/x{self.comId}/s/blog?type=user&q={userId}&start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))

    async def get_user_wikis(self, userId: str, start: int = 0, size: int = 25) -> List[Wiki]:
        response = await self.get(f"/x{self.comId}/s/item?type=user-all&start={start}&size={size}&cv=1.2&uid={userId}")
        return list(map(lambda o: Wiki(**o), (await response.json())["itemList"]))

    async def get_user_achievements(self, userId: str) -> Achievement:
        response = await self.get(f"/x{self.comId}/s/user-profile/{userId}/achievements")
        return Achievement(**(await response.json())["achievements"])

    async def get_influencer_fans(self, userId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/influencer/{userId}/fans?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())))

    async def get_blocked_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/block?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))

    async def get_blocker_users(self, start: int = 0, size: int = 25) -> List[str]:
        response = await self.get(f"/x{self.comId}/s/block?start={start}&size={size}")
        return loads(await response.text())["blockerUidList"]

    async def search_users(self, nickname: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/user-profile?type=name&q={nickname}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))

    async def get_saved_blogs(self, start: int = 0, size: int = 25) -> List[Bookmark]:
        response = await self.get(f"/x{self.comId}/s/bookmark?start={start}&size={size}")
        return list(map(lambda o: Bookmark(**o), (await response.json())["bookmarkList"]))
    
    async def get_leaderboard_info(self, type: int, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/g/s-x{self.comId}/community/leaderboard?rankingType={type}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))
    
    async def get_tipped_users(self, blogId: str = None, wikiId: str = None, 
            fileId: str = None, chatId: str = None, start: int = 0, size: int = 25) -> List[TippedUserSummary]:
        if blogId:
            url = f"/x{self.comId}/s/blog/{blogId}/tipping/tipped-users-summary?start={start}&size={size}"

        elif wikiId: 
            url = f"/x{self.comId}/s/item/{wikiId}/tipping/tipped-users-summary?start={start}&size={size}"

        elif chatId: 
            url = f"/x{self.comId}/s/chat/thread/{chatId}/tipping/tipped-users-summary?start={start}&size={size}"

        elif fileId: 
            url = f"/x{self.comId}/s/shared-folder/files/{fileId}/tipping/tipped-users-summary?start={start}&size={size}"

        else: raise SpecifyType()

        response = await self.get(url)
        return list(map(lambda o: TippedUserSummary(**o), await response.json()))
    
    async def get_chat_threads(self, start: int = 0, size: int = 25) -> List[Thread]:
        response = await self.get(f"/x{self.comId}/s/chat/thread?type=joined-me&start={start}&size={size}")
        return list(map(lambda o: Thread(**o), (await response.json())["threadList"]))

    async def get_public_chat_threads(self, type: str = "recommended", start: int = 0, size: int = 25) -> List[Thread]:
        response = await self.get(f"/x{self.comId}/s/chat/thread?type=public-all&filterType={type}&start={start}&size={size}")
        return list(map(lambda o: Thread(**o), (await response.json())["threadList"]))

    async def get_chat_thread(self, chatId: str) -> Thread:
        response = await self.get(f"/x{self.comId}/s/chat/thread/{chatId}")
        return Thread(loads(await response.json())["thread"])

    async def get_chat_messages(self, chatId: str, size: int = 25, pageToken: str = None) -> List[Message]:
        if not pageToken: params = f"v=2&pagingType=t&size={size}"
        else: params = f"v=2&pagingType=t&pageToken={pageToken}&size={size}"

        response = await self.get(f"/x{self.comId}/s/chat/thread/{chatId}/message?{params}")
        return list(map(lambda o: Message(**o, **data["paging"]), (data := await response.json())["messageList"]))

    async def get_message_info(self, chatId: str, messageId: str) -> Message:
        response = await self.get(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}")
        return Message(**(await response.json())["message"])
    
    async def get_blog_info(self, blogId: str = None, wikiId: str = None, fileId: str = None) -> Union[Wiki, Blog]:
        if blogId:
            response = await self.get(f"/x{self.comId}/s/blog/{blogId}")
            return Blog(**(await response.json()))

        elif wikiId:
            response = await self.get(f"/x{self.comId}/s/item/{wikiId}")
            return Wiki(**(await response.json()))

        elif fileId:
            response = await self.get(f"/x{self.comId}/s/shared-folder/files/{fileId}")
            return Wiki(**(await response.json())["file"])

        else: raise SpecifyType()
    
    async def get_blog_comments(self, blogId: str = None, wikiId: str = None, 
            fileId: str = None, sorting: str = "newest", start: int = 0, size: int = 25) -> List[Comment]:
        if blogId:
            url = f"/x{self.comId}/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}"

        elif wikiId:
            url = f"/x{self.comId}/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}"

        elif fileId:
            url = f"/x{self.comId}/s/shared-folder/files/{fileId}/comment?sort={sorting}&start={start}&size={size}"

        else: raise SpecifyType()

        response = await self.get(url)
        return list(map(lambda o: Comment(**o), (await response.json())["commentList"]))
    
    async def get_blog_categories(self, size: int = 25) -> List[BlogCategory]:
        response = await self.get(f"/x{self.comId}/s/blog-category?size={size}")
        return list(map(lambda o: BlogCategory(**o), (await response.json())["blogCategoryList"]))

    async def get_blogs_by_category(self, categoryId: str, start: int = 0, size: int = 25) -> List[Blog]:
        response = await self.get(f"/x{self.comId}/s/blog-category/{categoryId}/blog-list?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))

    async def get_quiz_rankings(self, quizId: str, start: int = 0, size: int = 25)-> QuizRanking:
        response = await self.get(f"/x{self.comId}/s/blog/{quizId}/quiz/result?start={start}&size={size}")
        return QuizRanking(**(await response.json()))
    
    async def get_wall_comments(self, userId: str, sorting: str, start: int = 0, size: int = 25) -> List[Comment]:
        response = await self.get(f"/x{self.comId}/s/user-profile/{userId}/comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), (await response.json())["commentList"]))

    async def get_recent_blogs(self, pageToken: str = None, start: int = 0, size: int = 25) -> Blog:
        if not pageToken: params = f"v=2&pagingType=t&start={start}&size={size}"
        else: params = f"v=2&pagingType=t&pageToken={pageToken}&start={start}&size={size}"
        
        response = await self.get(f"/x{self.comId}/s/feed/blog-all?{params}")
        return list(map(lambda o: Blog(**o, **data["paging"]), (data := await response.json())["blogList"]))

    async def get_chat_users(self, chatId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2")
        return list(map(lambda o: UserProfile(**o), (await response.json())["memberList"]))
    
    # TODO : Finish this
    async def get_notifications(self, start: int = 0, size: int = 25) -> dict:
        response = await self.get(f"/x{self.comId}/s/notification?pagingType=t&start={start}&size={size}")
        return (await response.json())["notificationList"]
    
    async def get_sticker_pack_info(self, sticker_pack_id: str) -> StickerCollection:
        response = await self.get(f"/x{self.comId}/s/sticker-collection/{sticker_pack_id}?includeStickers=true")
        return StickerCollection(**(await response.json())["stickerCollection"])

    async def get_sticker_packs(self) -> List[StickerCollection]:
        response = await self.get(f"/x{self.comId}/s/sticker-collection?includeStickers=false&type=my-active-collection")
        return list(map(lambda o: StickerCollection(**o), (await response.json())["stickerCollection"]))

    async def get_store_chat_bubbles(self, start: int = 0, size: int = 25) -> List[StoreItem]:
        response = await self.get(f"/x{self.comId}/s/store/items?sectionGroupId=chat-bubble&start={start}&size={size}")
        return list(map(lambda o: StoreItem(**o), (await response.json())["stickerCollection"]))

    async def get_store_stickers(self, start: int = 0, size: int = 25) -> List[StoreItem]:
        response = await self.get(f"/x{self.comId}/s/store/items?sectionGroupId=sticker&start={start}&size={size}")
        return list(map(lambda o: StoreItem(**o), (await response.json())["stickerCollection"]))
    
    async def get_community_stickers(self) -> List[StickerCollection]:
        response = await self.get(f"/x{self.comId}/s/sticker-collection?type=community-shared")
        return list(map(lambda o: StickerCollection(**o), (await response.json())))

    async def get_sticker_collection(self, collectionId: str) -> StickerCollection:
        response = await self.get(f"/x{self.comId}/s/sticker-collection/{collectionId}?includeStickers=true")
        return StickerCollection(**(await response.json())["stickerCollection"])

    # TODO : Finish this
    async def get_shared_folder_info(self) -> dict:
        response = await self.get(f"/x{self.comId}/s/shared-folder/stats")
        return (await response.json())["stats"]

    # TODO : Finish this
    async def get_shared_folder_files(self, type: str = "latest", start: int = 0, size: int = 25) -> dict:
        response = await self.get(f"/x{self.comId}/s/shared-folder/files?type={type}&start={start}&size={size}")
        return (await response.json())["fileList"]
    
    async def reorder_featured_users(self, userIds: list) -> int:
        data = {
            "uidList": userIds,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/user-profile/featured/reorder", data)
        return response.status

    async def get_hidden_blogs(self, start: int = 0, size: int = 25) -> Blog:
        response = await self.get(f"/x{self.comId}/s/feed/blog-disabled?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))

    async def get_featured_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/user-profile?type=featured&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"])) 

    async def review_quiz_questions(self, quizId: str) -> List[Blog.QuizQuestion]:
        response = await self.get(f"/x{self.comId}/s/blog/{quizId}?action=review")
        return list(map(lambda o: Blog.QuizQuestion(**o), (await response.json())["blog"]["quizQuestionList"]))

    async def get_recent_quiz(self, start: int = 0, size: int = 25) -> Blog:
        response = await self.get(f"/x{self.comId}/s/blog?type=quizzes-recent&start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))

    async def get_trending_quiz(self, start: int = 0, size: int = 25) -> Blog:
        response = await self.get(f"/x{self.comId}/s/feed/quiz-trending?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))

    async def get_best_quiz(self, start: int = 0, size: int = 25) -> Blog:
        response = await self.get(f"/x{self.comId}/s/feed/quiz-best-quizzes?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))
    
    async def moderation_history(self, userId: str = None, blogId: str = None, 
            wikiId: str = None, quizId: str = None, fileId: str = None, size: int = 25) -> List[AdminLog]:
        if userId:
            objectId = userId
            type = ObjectTypes.USER

        elif blogId:
            objectId = blogId
            type = ObjectTypes.BLOG

        elif quizId:
            objectId = quizId
            type = ObjectTypes.BLOG

        elif wikiId:
            objectId = wikiId
            type = ObjectTypes.ITEM

        elif fileId:
            objectId = fileId
            type = ObjectTypes.FOLDER_FILE

        else:
            objectId = None
            type = None

        response = await self.get(f"/x{self.comId}/s/admin/operation?pagingType=t&size={size}" \
            "?objectId={userId}&objectType={type}" if type and objectId else "")
        return list(map(lambda o: AdminLog(**o), (await response.json())["adminLogList"]))

    async def feature(self, seconds: int, userId: str = None,
            chatId: str = None, blogId: str = None, wikiId: str = None) -> int:
        data = {
            "adminOpName": 114,
            "adminOpValue": {
                "featuredDuration": seconds
            },
            "timestamp": int(time() * 1000)
        }

        if userId:
            data["adminOpValue"] = {"featuredType": FeaturedTypes.USER}
            response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
            return response.status

        elif blogId:
            data["adminOpValue"] = {"featuredType": FeaturedTypes.BLOG}
            response = await self.post(f"/x{self.comId}/s/blog/{blogId}/admin", data)
            return response.status

        elif wikiId:
            data["adminOpValue"] = {"featuredType": FeaturedTypes.WIKI}
            response = await self.post(f"/x{self.comId}/s/item/{wikiId}/admin", data)
            return response.status

        elif chatId:
            data["adminOpValue"] = {"featuredType": FeaturedTypes.CHAT}
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", data)
            return response.status

        else: raise SpecifyType()

    async def unfeature(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None) -> int:
        data = {
            "adminOpName": 114,
            "adminOpValue": {
                "featuredType": FeaturedTypes.UNFEATURE
            },
            "timestamp": int(time() * 1000)
        }

        if userId:
            response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
            return response.status

        elif blogId:
            response = await self.post(f"/x{self.comId}/s/blog/{blogId}/admin", data)
            return response.status

        elif wikiId:
            response = await self.post(f"/x{self.comId}/s/item/{wikiId}/admin", data)
            return response.status

        elif chatId:
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", data)
            return response.status

        else: raise SpecifyType()
    
    async def hide(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, reason: str = None) -> int:
        data = {
            "adminOpName": 110,
            "adminOpValue": 9,
            "adminOpNote": {
                "content": reason
            },
            "timestamp": int(time() * 1000)
        }

        if userId:
            data["adminOpName"] = 18
            response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
            return response.status

        elif blogId:
            response = await self.post(f"/x{self.comId}/s/blog/{blogId}/admin", data)
            return response.status

        elif quizId:
            response = await self.post(f"/x{self.comId}/s/blog/{quizId}/admin", data)
            return response.status

        elif wikiId:
            response = await self.post(f"/x{self.comId}/s/item/{wikiId}/admin", data)
            return response.status

        elif chatId:
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", data)
            return response.status

        elif fileId:
            response = await self.post(f"/x{self.comId}/s/shared-folder/files/{fileId}/admin", data)
            return response.status

        else: raise SpecifyType()

    async def unhide(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, reason: str = None) -> int:
        data = {
            "adminOpName": 110,
            "adminOpValue": 0,
            "adminOpNote": {
                "content": reason
            },
            "timestamp": int(time() * 1000)
        }

        if userId:
            data["adminOpName"] = 19
            response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
            return response.status

        elif blogId:
            response = await self.post(f"/x{self.comId}/s/blog/{blogId}/admin", data)
            return response.status

        elif quizId:
            response = await self.post(f"/x{self.comId}/s/blog/{quizId}/admin", data)
            return response.status

        elif wikiId:
            response = await self.post(f"/x{self.comId}/s/item/{wikiId}/admin", data)
            return response.status

        elif chatId:
            response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", data)
            return response.status

        elif fileId:
            response = await self.post(f"/x{self.comId}/s/shared-folder/files/{fileId}/admin", data)
            return response.status

        else: raise SpecifyType()

    async def edit_titles(self, userId: str, titles: list, colors: list) -> int:
        titles = [{"title": titles, "color": colors} for titles, colors in zip(titles, colors)]

        data = {
            "adminOpName": 207,
            "adminOpValue": {
                "titles": titles
            },
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
        return response.status

    # TODO : List all warning texts
    async def warn(self, userId: str, reason: str = None) -> int:
        data = {
            "uid": userId,
            "title": "Custom",
            "content": reason,
            "attachedObject": {
                "objectId": userId,
                "objectType": ObjectTypes.USER
            },
            "penaltyType": 0,
            "adminOpNote": {},
            "noticeType": 7,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/notice", data)
        return response.status

    # TODO : List all strike texts
    async def strike(self, userId: str, seconds: int, title: str = None, reason: str = None) -> int:
        data = {
            "uid": userId,
            "title": title,
            "content": reason,
            "attachedObject": {
                "objectId": userId,
                "objectType": ObjectTypes.USER
            },
            "penaltyType": 1,
            "penaltyValue": seconds,
            "adminOpNote": {},
            "noticeType": 4,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/notice", data)
        return response.status
    
    async def ban(self, userId: str, reason: str, banType: int = None) -> int:
        data = {
            "reasonType": banType,
            "note": {
                "content": reason
            },
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/ban", data)
        return response.status

    async def unban(self, userId: str, reason: str) -> int:
        data = {
            "note": {
                "content": reason
            },
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/user-profile/{userId}/unban", data)
        return response.status
    
    async def purchase(self, objectId: str, objectType: int, autoRenew: bool = False) -> int:
        data = {
            "v": 1,
            "objectId": objectId,
            "objectType": objectType,
            "paymentContext": {
                "discountStatus": 1, 
                "discountValue": 1, 
                "isAutoRenew": autoRenew
            },
            "timestamp": int(time() * 1000)
        }

        if self.profile.membershipStatus == 0:
            data["paymentContext"]["discountStatus"] = 0

        response = await self.post(f"/x{self.comId}/s/store/purchase", data)
        return response.status
    
    async def invite_to_vc(self, chatId: str, userId: str) -> int:
        data = {
            "uid": userId
        }

        response = await self.post(f"/x{self.comId}/s/chat/thread/{chatId}/vvchat-presenter/invite", data)
        return response.status

    async def add_poll_option(self, blogId: str, question: str) -> int:
        data = {
            "mediaList": None,
            "title": question,
            "type": 0,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/blog/{blogId}/poll/option", data)
        return response.status

    async def create_wiki_category(self, title: str, parentCategoryId: str, content: str = None) -> int:
        data = {
            "content": content,
            "icon": None,
            "label": title,
            "mediaList": None,
            "parentCategoryId": parentCategoryId,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/item-category", data)
        return response.status

    async def create_shared_folder(self, title: str) -> int:
        data = {
            "title": title,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/shared-folder/folders", data)
        return response.status

    async def submit_to_wiki(self, wikiId: str, message: str) -> int:
        data = {
            "message": message,
            "itemId": wikiId,
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/knowledge-base-request", data)
        return response.status

    async def accept_wiki_request(self, requestId: str, destinationCategoryIdList: list) -> int:
        data = {
            "destinationCategoryIdList": destinationCategoryIdList,
            "actionType": "create",
            "timestamp": int(time() * 1000)
        }

        response = await self.post(f"/x{self.comId}/s/knowledge-base-request/{requestId}/approve", data)
        return response.status

    async def apply_avatar_frame(self, avatarId: str, applyToAll: bool = True) -> int:
        data = {
            "frameId": avatarId,
            "applyToAll": 0,
            "timestamp": int(time() * 1000)
        }

        if applyToAll:
            data["applyToAll"] = 1

        response = await self.post(f"/x{self.comId}/s/avatar-frame/apply", data)
        return response.status
    
    async def apply_chat_bubble(self, bubbleId: str, chatId: str, applyToAll: bool = False) -> int:
        data = {
            "applyToAll": 0,
            "bubbleId": bubbleId,
            "threadId": chatId,
            "timestamp": int(time() * 1000)
        }

        if applyToAll:
            data["applyToAll"] = 1

        response = await self.post(f"/x{self.comId}/s/chat/thread/apply-bubble", data)
        return response.status

    async def reject_wiki_request(self, requestId: str) -> int:
        response = await self.post(f"/x{self.comId}/s/knowledge-base-request/{requestId}/reject")
        return response.status

    # TODO : Finish this
    async def get_wiki_submissions(self, start: int = 0, size: int = 25) -> dict:
        response = await self.get(f"/x{self.comId}/s/knowledge-base-request?type=all&start={start}&size={size}")
        return (await response.json())["knowledgeBaseRequestList"]
    
    # Live Layer (i dont enf this)
    async def get_live_layer(self) -> dict:
        response = await self.get(f"/x{self.comId}/s/live-layer/homepage?v=2")
        return (await response.text())["liveLayerList"]
    
    async def get_online_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))
    
    async def get_online_users_count(self) -> int:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start=0&size=1")
        return (await response.json())["userProfileCount"]
    
    async def get_public_chats(self, start: int = 0, size: int = 25) -> List[Thread]:
        response = await self.get(f"/x{self.comId}/s/live-layer/public-chats?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["threadList"]))
    
    async def get_chatting_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-chatting&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))
    
    async def get_chatting_users_count(self) -> int:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-chatting&start=0&size=1")
        return (await response.json())["userProfileCount"]

    async def get_live_chats(self, start: int = 0, size: int = 25) -> List[Thread]:
        response = await self.get(f"/x{self.comId}/s/live-layer/public-live-chats?start={start}&size={size}")
        return list(map(lambda o: Thread(**o), (await response.json())["threadList"]))
    
    async def get_live_chatting_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-live-chatting&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))
    
    async def get_live_chatting_users_count(self) -> int:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-live-chatting&start=0&size=1")
        return (await response.json())["userProfileCount"]

    async def get_playing_quizzes(self, start: int = 0, size: int = 25) -> List[Blog]:
        response = await self.get(f"/x{self.comId}/s/live-layer/quizzes?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))
    
    async def get_playing_quizzes_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-playing-quizzes&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))
    
    async def get_playing_quizzes_users_count(self) -> int:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-playing-quizzes&start=0&size=1")
        return (await response.json())["userProfileCount"]

    async def get_browsing_blogs(self, start: int = 0, size: int = 25) -> List[Blog]:
        response = await self.get(f"/x{self.comId}/s/live-layer/blogs?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), (await response.json())["blogList"]))
    
    async def get_browsing_blogs_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-browsing-blogs&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))
    
    async def get_browsing_blogs_users_count(self) -> int:
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-browsing-blogs&start=0&size=1")
        return (await response.json())["userProfileCount"]

    async def get_blog_users(self, blogId: str, start: int = 0, size: int = 25):
        response = await self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic%3Ax{self.comId}%3Ausers-browsing-blog-at%3A{blogId}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), (await response.json())["userProfileList"]))
    
    # Live Layer (i dont enf this)

    async def activate_bubble(self, bubbleId: str) -> int:
        response = await self.post(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}/activate")
        return response.status

    async def deactivate_bubble(self, bubbleId: str) -> int:
        response = await self.post(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}/deactivate")
        return response.status    
    
    async def get_chat_bubbles(self, chatId: str, start: int = 25, size: int = 25) -> List[ChatBubble]:
        response = await self.get(f"/x{self.comId}/s/chat/chat-bubble?type=all-my-bubbles?threadId={chatId}?start={start}?size={size}")
        return list(map(lambda o: ChatBubble(**o), (await response.json())["chatBubbleList"]))
    
    async def get_chat_bubble(self, bubbleId: str) -> ChatBubble:
        response = await self.get(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}")
        return ChatBubble(**(await response.json())["chatBubble"])

    async def get_chat_bubble_templates(self, start: int = 0, size: int = 25) -> List[ChatBubble]:
        response = await self.get(f"/x{self.comId}/s/chat/chat-bubble/templates?start={start}&size={size}")
        return list(map(lambda o: ChatBubble(**o), (await response.json())["templateList"]))
    
    async def generate_chat_bubble(self, bubble: bytes = None, 
            templateId: str = "949156e1-cc43-49f0-b9cf-3bbbb606ad6e") -> ChatBubble:
        response = await self.post(f"/x{self.comId}/s/chat/chat-bubble/templates/{templateId}/generate", data=bubble, type=FileTypes.STREAM)
        return ChatBubble(**(await response.json())["chatBubble"])
    
    async def edit_chat_bubble(self, bubbleId: str, bubble: bytes) -> ChatBubble:
        response = await self.post(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}", data=bubble, type=FileTypes.STREAM)
        return ChatBubble(**(await response.json())["chatBubble"])

    async def send_active_object(self, timers: List[dict], timezone: int = 0, flags: int = 0):
        data = {
            "userActiveTimeChunkList": timers, 
            "optInAdsFlags": flags, 
            "timestamp": int(time() * 1000), 
            "timezone": timezone
        }

        data = json_minify(dumps(data))
        response = await self.post(f"/x{self.comId}/s/community/stats/user-active-time", data=data)
        return response.status


from base64 import b64encode
from time import time, timezone
from typing import Callable, Union, List
from uuid import uuid4
from requests import Session
from json_minify import json_minify
from ujson import dumps, loads

from .utils.models import *
from .utils.types import *
from .utils.helpers import *
from .utils.exceptions import *
from .http_client import AminoHttpClient


class CommunityClient(AminoHttpClient):
    def __init__(self, comId: int,
        session: Optional[Session] = None, 
        info: Optional[Community] = None,
        settings: Optional[dict] = None,
        proxies: Optional[dict] = None,
        timeout: Optional[int] = 60
    ) -> None:
        self._session: Session = session or Session()
        
        self.comId = comId
        self.headers = settings or self.headers

        self.proxies: Optional[str] = proxies
        self.timeout: Optional[int] = timeout
        
        self.profile: UserProfile = UserProfile(**{})
        self.info: Community = info or Community(**{})

    def __enter__(self) -> "CommunityClient":
        return self

    def __exit__(self, *args) -> None:
        return
    
    # this is an experimental test function, 
    # use it, but be aware that there may be problems with it.
    async def with_proxy(self, proxies: dict, func: Callable, *args):
        client: 'CommunityClient' = getattr(sys.modules[__name__], "CommunityClient")(
            self.comId, None, self.info, self.headers, proxies, self.timeout)
        
        if func.__name__ in client.__dir__():
            args = list(args)
            
            for arg in args:
                if isinstance(arg, str):
                    args[args.index(arg)] = f"'{arg}'"
                else:
                    args[args.index(arg)] = str(arg) 
                    
            func = f"client.{func.__name__}({','.join(args)})"
            
            return eval(func)
        else:
            raise Exception("Its func not in aminoed.CommunityClient class.")
    
    def get_invite_codes(self, status: str = "normal", start: int = 0, size: int = 25) -> List[InviteCode]:
        response = self.get(f"/g/s-x{self.comId}/community/invitation?status={status}&start={start}&size={size}")
        return list(map(lambda o: InviteCode(**o), response.json()["communityInvitationList"]))

    def get_user_info(self, userId: str) -> UserProfile:
        response = self.get(f"/x{self.comId}/s/user-profile/{userId}")
        return UserProfile(**response.json()["userProfile"])

    def generate_invite_code(self, duration: int = 0, force: bool = True):
        data = {
            "duration": duration,
            "force": force
        }

        response = self.post(f"/g/s-x{self.comId}/community/invitation", data)
        return InviteCode(**response.json()["communityInvitation"])

    def delete_invite_code(self, inviteId: str) -> int:
        response = self.delete(f"/g/s-x{self.comId}/community/invitation/{inviteId}")
        return response.status_code
    
    def delete_blog(self, blogId: str) -> int:
        response = self.delete(f"/x{self.comId}/s/blog/{blogId}")
        return response.status_code

    def delete_wiki(self, wikiId: str) -> int:
        response = self.delete(f"/x{self.comId}/s/item/{wikiId}")
        return response.status_code
    
    def upload_media(self, file: bytes, fileType: str = FileTypes.IMAGE) -> str:
        response = self.post(f"/x{self.comId}/s/media/upload", data=file, type=fileType)
        return response.json()["mediaValue"]

    def post_blog(self, title: str, content: str, imageList: list = None, captionList: list = None, 
            categoriesList: list = None, backgroundColor: str = None, fansOnly: bool = False, extensions: dict = None) -> int:
        if captionList and imageList:
            mediaList = [[100, self.upload_media(image), caption] for image, caption in zip(imageList, captionList)]

        elif imageList:
            mediaList = [[100, self.upload_media(image), None] for image in imageList]

        data = {
            "address": None,
            "content": content,
            "title": title,
            "mediaList": mediaList,
            "extensions": extensions,
            "latitude": 0,
            "longitude": 0,
            "eventSource": SourceTypes.GLOBAL_COMPOSE
        }

        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if categoriesList: data["taggedBlogCategoryIdList"] = categoriesList

        response = self.post(f"/x{self.comId}/s/blog", data)
        return response.status_code
    
    def post_wiki(self, title: str, content: str, icon: str = None, imageList: list = None,
            keywords: str = None, backgroundColor: str = None, fansOnly: bool = False) -> int:

        mediaList = [[100, self.upload_media(image), None] for image in imageList]

        data = {
            "label": title,
            "content": content,
            "mediaList": mediaList,
            "eventSource": SourceTypes.GLOBAL_COMPOSE
        }

        if icon: data["icon"] = icon
        if keywords: data["keywords"] = keywords
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}

        response = self.post(f"/x{self.comId}/s/item", data)
        return response.status_code

    def edit_blog(self, blogId: str, title: str = None, content: str = None, imageList: list = None, 
            categoriesList: list = None, backgroundColor: str = None, fansOnly: bool = False) -> int:
        mediaList = [[100, self.upload_media(image), None] for image in imageList]

        data = {
            "address": None,
            "mediaList": mediaList,
            "latitude": 0,
            "longitude": 0,
            "eventSource": "PostDetailView"
        }

        if title: data["title"] = title
        if content: data["content"] = content
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if categoriesList: data["taggedBlogCategoryIdList"] = categoriesList

        response = self.post(f"/x{self.comId}/s/blog/{blogId}", data)
        return response.status_code
    
    def repost_blog(self, content: str = None, blogId: str = None, wikiId: str = None) -> int:
        if blogId:
            refObjectId, refObjectType = blogId, ObjectTypes.BLOG
        elif wikiId: 
            refObjectId, refObjectType = wikiId, ObjectTypes.ITEM
        else: raise SpecifyType()

        data = {
            "content": content,
            "refObjectId": refObjectId,
            "refObjectType": refObjectType,
            "type": 2
        }

        response = self.post(f"/x{self.comId}/s/blog", data)
        return response.status_code
    
    def check_in(self, tz: int = -timezone // 1000) -> CheckIn:
        data = {
            "timezone": tz
        }

        response = self.post(f"/x{self.comId}/s/check-in", data)
        return CheckIn(**response.json())

    def repair_check_in(self, method: int = RepairTypes.COINS) -> int:
        data = {
            "repairMethod": method
        }
        response = self.post(f"/x{self.comId}/s/check-in/repair", data)
        return response.status_code

    def lottery(self, tz: int = -timezone // 1000) -> int:
        data = {
            "timezone": tz
        }

        response = self.post(f"/x{self.comId}/s/check-in/lottery", data)
        return Lottery(**response.json()["lotteryLog"])
    
    def edit_profile(self, nickname: str = None, content: str = None, icon: bytes = None, chatRequestPrivilege: str = None, 
            imageList: list = None, captionList: list = None, backgroundImage: str = None, backgroundColor: str = None, 
            titles: list = None, colors: list = None, defaultBubbleId: str = None) -> int:
        data = {}

        if captionList and imageList:
            mediaList = [[100, self.upload_media(image), caption] for image, caption in zip(imageList, captionList)]

        elif imageList:
            mediaList = [[100, self.upload_media(image), None] for image in imageList]

        if imageList or captionList and imageList:
            data["mediaList"] = mediaList

        if nickname: data["nickname"] = nickname

        if icon:
            if isinstance(icon, str):
                data["icon"] = icon

            if isinstance(icon, bytes):
                data["icon"] = self.upload_media(icon)

            else: raise SpecifyType()

        if backgroundImage:
            if isinstance(backgroundImage, str):
                data["extensions"] = {"style": {
                    "backgroundMediaList": [[100, backgroundImage, None, None, None]]}}

            if isinstance(backgroundImage, bytes):
                image = self.upload_media(backgroundImage)
                data["extensions"] = {"style": {"backgroundMediaList": [[100, image, None, None, None]]}}

            else: raise SpecifyType()

        if content: data["content"] = content

        if chatRequestPrivilege: data["extensions"] = {"privilegeOfChatInviteRequest": chatRequestPrivilege}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if defaultBubbleId: data["extensions"] = {"defaultBubbleId": defaultBubbleId}

        if titles or colors:
            tlt = [{"title": titles, "color": colors} for titles, colors in zip(titles, colors)]
            data["extensions"] = {"customTitles": tlt}

        response = self.post(f"/x{self.comId}/s/user-profile/{self.userId}", data)
        return response.status_code
    
    def vote_poll(self, blogId: str, optionId: str) -> int:
        data = {
            "value": 1,
            "eventSource": SourceTypes.DATAIL_POST
        }

        response = self.post(f"/x{self.comId}/s/blog/{blogId}/poll/option/{optionId}/vote", data)
        return response.status_code
    
    def comment(self, message: str, userId: str = None, 
            blogId: str = None, wikiId: str = None, replyTo: str = None) -> int:
        data = {
            "content": message,
            "stickerId": None,
            "type": 0
        }

        if replyTo:
            data["respondTo"] = replyTo

        if userId:
            data["eventSource"] = SourceTypes.USER_PROFILE
            response = self.post(f"/x{self.comId}/s/user-profile/{userId}/g-comment", data)
            return response.status_code

        elif blogId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = self.post(f"/x{self.comId}/s/blog/{blogId}/g-comment", data)
            return response.status_code

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = self.post(f"/x{self.comId}/s/item/{wikiId}/g-comment", data)
            return response.status_code

        else: raise SpecifyType()
    
    def delete_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
        if userId: url = f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}"
        elif blogId: url = f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}"
        elif wikiId: url = f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}"
        else: raise SpecifyType()

        response = self.delete(url)
        return response.status_code
    
    def like_blog(self, blogId: Union[str, list] = None, wikiId: str = None) -> int:
        data = {
            "value": 4
        }

        if blogId:
            if isinstance(blogId, str):
                data["eventSource"] = SourceTypes.USER_PROFILE
                response = self.post(f"/x{self.comId}/s/blog/{blogId}/g-vote?cv=1.2", data)
                return response.status_code

            elif isinstance(blogId, list):
                data["targetIdList"] = blogId
                response = self.post(f"/x{self.comId}/s/feed/g-vote", data)
                return response.status_code

            else: raise WrongType(type(blogId))

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = self.post(f"/x{self.comId}/s/item/{wikiId}/g-vote?cv=1.2", data)
            return response.status_code

        else: raise SpecifyType()

    def unlike_blog(self, blogId: str = None, wikiId: str = None) -> int:
        if blogId:
            url = f"/x{self.comId}/s/blog/{blogId}/vote?eventSource=UserProfileView"

        elif wikiId:
            url = f"/x{self.comId}/s/item/{wikiId}/vote?eventSource=PostDetailView"

        else: raise SpecifyType()

        response = self.delete(url)
        return response.status_code
    
    def like_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
        data = {
            "value": 4
        }

        if userId:
            data["eventSource"] = SourceTypes.USER_PROFILE
            response = self.post(f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
            return response.status_code

        elif blogId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = self.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
            return response.status_code

        elif wikiId:
            data["eventSource"] = SourceTypes.DATAIL_POST
            response = self.post(f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/g-vote?cv=1.2&value=1", data)
            return response.status_code

        else: raise SpecifyType()
    
    def unlike_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
        if userId: 
            url = f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView"

        elif blogId: 
            url = f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView"

        elif wikiId: 
            url = f"/g/s/item/{wikiId}/comment/{commentId}/g-vote?eventSource=PostDetailView"

        else: raise SpecifyType()

        response = self.delete(url)
        return response.status_code
    
    def upvote_comment(self, blogId: str, commentId: str) -> int:
        data = {
            "value": 1,
            "eventSource": "PostDetailView"
        }

        response = self.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1", data)
        return response.status_code

    def downvote_comment(self, blogId: str, commentId: str) -> int:
        data = {
            "value": -1,
            "eventSource": "PostDetailView"
        }

        response = self.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=-1", data)
        return response.status_code

    def unvote_comment(self, blogId: str, commentId: str) -> int:
        response = self.delete(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?eventSource=PostDetailView")
        return response.status_code
    
    def reply_wall(self, userId: str, commentId: str, message: str) -> int:
        data = {
            "content": message,
            "stackedId": None,
            "respondTo": commentId,
            "type": 0,
            "eventSource": "UserProfileView"
        }

        response = self.post(f"/x{self.comId}/s/user-profile/{userId}/comment", data)
        return response.status_code

    def activity_status(self, status: int) -> int:
        data = {
            "onlineStatus": status,
            "duration": 86400
        }

        response = self.post(f"/x{self.comId}/s/user-profile/{self.userId}/online-status", data)
        return response.status_code
    
    def check_notifications(self) -> int:
        response = self.post(f"/x{self.comId}/s/notification/checked")
        return response.status_code

    def delete_notification(self, notificationId: str) -> int:
        response = self.delete(f"/x{self.comId}/s/notification/{notificationId}")
        return response.status_code

    def clear_notifications(self) -> int:
        response = self.delete(f"/x{self.comId}/s/notification")
        return response.status_code
    
    def start_chat(self, userId: Union[str, list], message: str, title: str = None,
            content: str = None, isGlobal: bool = False, publishToGlobal: bool = False) -> Thread:
        data = {
            "title": title,
            "inviteeUids": userId if isinstance(userId, list) else [userId],
            "initialMessageContent": message,
            "content": content
        }

        if isGlobal: 
            data["type"] = ChatPublishTypes.IS_GLOBAL
            data["eventSource"] = SourceTypes.GLOBAL_COMPOSE
        else: data["type"] = ChatPublishTypes.OFF

        if publishToGlobal: 
            data["publishToGlobal"] = ChatPublishTypes.ON
        else: data["publishToGlobal"] = ChatPublishTypes.OFF

        response = self.post(f"/x{self.comId}/s/chat/thread", data)
        return Thread(**response.json()["thread"])
    
    def invite_to_chat(self, userId: Union[str, list], chatId: str) -> int:
        data = {
            "uids": userId if isinstance(userId, list) else [userId]
        }

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/invite", data)
        return response.status_code

    def add_to_favorites(self, userId: str) -> int:
        response = self.post(f"/x{self.comId}/s/user-group/quick-access/{userId}")
        return response.status_code
    
    def send_coins(self, coins: int, blogId: str = None,
            chatId: str = None, objectId: str = None, transactionId: str = None) -> int:
        data = {
            "coins": coins,
            "tippingContext": {
                "transactionId": transactionId or str(uuid4())
            }
        }

        if blogId:
            response = self.post(f"/x{self.comId}/s/blog/{blogId}/tipping", data)
            return response.status_code
        
        elif chatId:
            response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping", data)
            return response.status_code
        
        elif objectId:
            data["objectId"] = objectId
            data["objectType"] = ObjectTypes.ITEM
            response = self.post(f"/x{self.comId}/s/tipping", data)
            return response.status_code
        
        else: SpecifyType() 

    def thank_tip(self, chatId: str, userId: str) -> int:
        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping/tipped-users/{userId}/thank")
        return response.status_code
    
    def follow(self, userId: Union[str, list]) -> int:
        if isinstance(userId, str):
            response = self.post(f"/x{self.comId}/s/user-profile/{userId}/member")
            return response.status_code

        elif isinstance(userId, list):
            data = {"targetUidList": userId}
            response = self.post(f"/x{self.comId}/s/user-profile/{self.userId}/joined", data)
            return response.status_code

        else: raise WrongType(type(userId))

    def unfollow(self, userId: str) -> int:
        response = self.delete(f"/x{self.comId}/s/user-profile/{self.userId}/joined/{userId}")
        return response.status_code
    
    def block(self, userId: str) -> int:
        response = self.post(f"/x{self.comId}/s/block/{userId}")
        return response.status_code

    def unblock(self, userId: str) -> int:
        response = self.delete(f"/x{self.comId}/s/block/{userId}")
        return response.status_code
    
    def flag(self, reason: str, flagType: int, userId: str = None,
            blogId: str = None, wikiId: str = None) -> int:
        if reason is None: raise ReasonNeeded
        if flagType is None: raise FlagTypeNeeded

        data = {
            "flagType": flagType,
            "message": reason
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

        response = self.post(f"/x{self.comId}/s/flag", data)
        return response.status_code
    
    def send_message(self, chatId: str, message: str = None, type: int = 0, replyTo: str = None, 
            mentions: list = None, embedId: str = None, embedType: int = None, embedLink: str = None, 
            embedTitle: str = None, embedContent: str = None, embedImage: Union[bytes, str] = None) -> Message:

        message = message.replace("<$", "‎‏")
        message = message.replace("$>", "‬‭")
        mentions = [{"uid": uid} for uid in mentions if mentions] if mentions else None

        if embedImage:
            if isinstance(embedImage, str):
                embedImage = [[100, embedImage, None]]
            elif isinstance(embedImage, bytes):
                embedImage = [[100, self.upload_media(embedImage), None]]
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
            "extensions": {"mentionedArray": mentions}
        }

        if replyTo:
            data["replyMessageId"] = replyTo

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Message(**response.json()["message"])
    
    def send_image(self, chatId: str, file: bytes) -> Message:
        data = {
            "type": 0,
            "mediaType": 100,
            "mediaUhqEnabled": True,
            "clientRefId": int(time() / 10 % 1000000000)
        }

        data["mediaUploadValueContentType"] = FileTypes.IMAGE
        data["mediaUploadValue"] = b64encode(file).decode()

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Message(**response.json()["message"])
    
    def send_audio(self, chatId: str, file: bytes) -> Message:
        data = {
            "type": 2,
            "mediaType": 110,
            "clientRefId": int(time() / 10 % 1000000000)
        }

        data["mediaUploadValueContentType"] = FileTypes.AUDIO
        data["mediaUploadValue"] = b64encode(file).decode()

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Message(**response.json()["message"])
    
    def send_sticker(self, chatId: str, stickerId: str) -> Message:
        data = {
            "type": 3,
            "stickerId": stickerId,
            "clientRefId": int(time() / 10 % 1000000000)
        }

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", data)
        return Message(**response.json()["message"])
    
    def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: str = None) -> int:
        data = {
            "adminOpName": 102,
            "adminOpNote": {"content": reason}
        }

        if asStaff and reason:
            data["adminOpNote"] = {"content": reason}

        if not asStaff:
            response = self.delete(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}")
            return response.status_code

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}/admin", data)
        return response.status_code
    
    def mark_as_read(self, chatId: str, messageId: str):
        data = {
            "messageId": messageId
        }

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/mark-as-read", data)
        return response.status_code
    
    def edit_chat(self, chatId: str, doNotDisturb: bool = None, pinChat: bool = None, 
            title: str = None, icon: Union[bytes, str] = None, backgroundImage: Union[bytes, str] = None, content: str = None, 
            announcement: str = None, coHosts: list = None, keywords: list = None, pinAnnouncement: bool = None, 
            publishToGlobal: bool = None, canTip: bool = None, viewOnly: bool = None, canInvite: bool = None, fansOnly: bool = None) -> int:
        data = {}
        responses = []

        if title: data["title"] = title
        if content: data["content"] = content
        
        if icon:
            if isinstance(icon, str):
                data["icon"] = icon

            elif isinstance(icon, bytes):
                data["icon"] = self.upload_media(icon)
            
            else: raise SpecifyType()
        
        if backgroundImage:
            if isinstance(backgroundImage, str):
                data = {"media": [100, backgroundImage, None]}
                response = self.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}/background", data)
                responses.append(response.status_code)

            elif isinstance(backgroundImage, bytes):
                data = {"media": [100, self.upload_media(backgroundImage), None]}
                response = self.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}/background", data)
                responses.append(response.status_code)
            
            else: raise SpecifyType()

        if keywords: data["keywords"] = keywords
        if announcement: data["extensions"] = {"announcement": announcement}
        if pinAnnouncement: data["extensions"] = {"pinAnnouncement": pinAnnouncement}
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}

        if publishToGlobal: data["publishToGlobal"] = 0
        if not publishToGlobal: data["publishToGlobal"] = 1

        if coHosts:
            data = {"uidList": coHosts}
            response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/co-host", data)
            responses.append(response.status_code)

        if doNotDisturb is True:
            data = {"alertOption": 2}
            response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}/alert", data)
            responses.append(response.status_code)

        if doNotDisturb is False:
            data = {"alertOption": 1}
            response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}/alert", data)
            responses.append(response.status_code)
        
        if pinChat is True: responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}/pin", data)).status)
        if pinChat is False: responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}/unpin", data)).status)

        if viewOnly is True: responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/enable", data)).status)
        if viewOnly is False: responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/disable", data)).status)

        if canInvite is True: responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/enable", data)).status)
        if canInvite is False: responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/disable", data)).status)

        if canTip is True: responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/enable", data)).status)
        if canTip is False: responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/disable", data)).status)

        responses.append((self.post(f"/x{self.comId}/s/chat/thread/{chatId}", data)).status)
        return int(sum(responses) / len(responses))
    
    def transfer_organizer(self, chatId: str, userIds: list) -> int:
        data = {
            "uidList": userIds
        }

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer", data)
        return response.status_code

    def accept_organizer(self, chatId: str, requestId: str) -> int:
        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept", {})
        return response.status_code

    def kick(self, userId: str, chatId: str, allowRejoin: bool = True) -> int:
        if allowRejoin: allowRejoin = 1
        if not allowRejoin: allowRejoin = 0

        response = self.delete(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}?allowRejoin={allowRejoin}")
        return response.status_code

    def join_chat(self, chatId: str) -> int:
        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}", {})
        return response.status_code

    def leave_chat(self, chatId: str) -> int:
        response = self.delete(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}")
        return response.status_code
        
    def delete_chat(self, chatId: str) -> int:
        response = self.delete(f"/x{self.comId}/s/chat/thread/{chatId}")
        return response.status_code
    
    def subscribe(self, userId: str, autoRenew: str = False, transactionId: str = None) -> int:
        data = {
            "paymentContext": {
                "transactionId": transactionId or str(uuid4()),
                "isAutoRenew": autoRenew
            }
        }

        response = self.post(f"/x{self.comId}/s/influencer/{userId}/subscribe", data)
        return response.status_code

    def promotion(self, noticeId: str, type: str = "accept") -> int:
        response = self.post(f"/x{self.comId}/s/notice/{noticeId}/{type}")
        return response.status_code

    def play_quiz_raw(self, quizId: str, quizAnswerList: list, quizMode: int = 0) -> int:
        data = {
            "mode": quizMode,
            "quizAnswerList": quizAnswerList
        }

        response = self.post(f"/x{self.comId}/s/blog/{quizId}/quiz/result", data)
        return response.status_code
    
    def play_quiz(self, quizId: str, questionIdsList: list, answerIdsList: list, quizMode: int = 0) -> int:
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
            "quizAnswerList": quizAnswerList
        }

        response = self.post(f"/x{self.comId}/s/blog/{quizId}/quiz/result", data)
        return response.status_code
    
    def vc_permission(self, chatId: str, permission: int) -> int:
        data = {
            "vvChatJoinType": permission
        }

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/vvchat-permission", data)
        return response.status_code

    def get_vc_reputation_info(self, chatId: str) -> VcReputation:
        response = self.get(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation")
        return VcReputation(**response.json())

    def claim_vc_reputation(self, chatId: str) -> VcReputation:
        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation")
        return VcReputation(**response.json())
    
    def get_all_users(self, type: str = "recent", start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/user-profile?type={type}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))

    def get_online_favorite_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/user-group/quick-access?type=online&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))

    def get_user_following(self, userId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/user-profile/{userId}/joined?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))

    def get_user_followers(self, userId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/user-profile/{userId}/member?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))

    def get_user_checkins(self, userId: str) -> List[CheckIn]:
        response = self.get(f"/x{self.comId}/s/check-in/stats/{userId}?timezone={-timezone // 1000}")
        return list(map(lambda o: CheckIn(**o), response.json()))

    def get_user_blogs(self, userId: str, start: int = 0, size: int = 25) -> List[Blog]:
        response = self.get(f"/x{self.comId}/s/blog?type=user&q={userId}&start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response.json()["blogList"]))

    def get_user_wikis(self, userId: str, start: int = 0, size: int = 25) -> List[Wiki]:
        response = self.get(f"/x{self.comId}/s/item?type=user-all&start={start}&size={size}&cv=1.2&uid={userId}")
        return list(map(lambda o: Wiki(**o), response.json()["itemList"]))

    def get_user_achievements(self, userId: str) -> Achievement:
        response = self.get(f"/x{self.comId}/s/user-profile/{userId}/achievements")
        return Achievement(**response.json()["achievements"])

    def get_influencer_fans(self, userId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/influencer/{userId}/fans?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()))

    # def get_blocked_users(self, start: int = 0, size: int = 25) -> List[str]:
    #     response = self.get(f"/x{self.comId}/s/block?start={start}&size={size}")
    #     return response.json()

    # def get_blocker_users(self, start: int = 0, size: int = 25) -> List[str]:
    #     response = self.get(f"/x{self.comId}/s/block?start={start}&size={size}")
    #     return response.json()
    # I make it in next updates
    
    def search_users(self, nickname: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/user-profile?type=name&q={nickname}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))

    def get_saved_blogs(self, start: int = 0, size: int = 25) -> List[Bookmark]:
        response = self.get(f"/x{self.comId}/s/bookmark?start={start}&size={size}")
        return list(map(lambda o: Bookmark(**o), response.json()["bookmarkList"]))
    
    def get_leaderboard_info(self, type: int, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/g/s-x{self.comId}/community/leaderboard?rankingType={type}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))
    
    def get_tipped_users(self, blogId: str = None, wikiId: str = None, 
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

        response = self.get(url)
        return list(map(lambda o: TippedUserSummary(**o), response.json()))
    
    def get_chat_threads(self, start: int = 0, size: int = 25) -> List[Thread]:
        response = self.get(f"/x{self.comId}/s/chat/thread?type=joined-me&start={start}&size={size}")
        return list(map(lambda o: Thread(**o), response.json()["threadList"]))

    def get_public_chat_threads(self, type: str = "recommended", start: int = 0, size: int = 25) -> List[Thread]:
        response = self.get(f"/x{self.comId}/s/chat/thread?type=public-all&filterType={type}&start={start}&size={size}")
        return list(map(lambda o: Thread(**o), response.json()["threadList"]))

    def get_chat_thread(self, chatId: str) -> Thread:
        response = self.get(f"/x{self.comId}/s/chat/thread/{chatId}")
        return Thread(**response.json()["thread"])

    def get_chat_messages(self, chatId: str, size: int = 25, pageToken: str = None) -> List[Message]:
        if not pageToken: params = f"v=2&pagingType=t&size={size}"
        else: params = f"v=2&pagingType=t&pageToken={pageToken}&size={size}"

        response = self.get(f"/x{self.comId}/s/chat/thread/{chatId}/message?{params}")
        return list(map(lambda o: Message(**o, **data["paging"]), (data := response.json())["messageList"]))

    def get_message_info(self, chatId: str, messageId: str) -> Message:
        response = self.get(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}")
        return Message(**response.json()["message"])
    
    def get_blog_info(self, blogId: str = None, wikiId: str = None, fileId: str = None) -> Union[Wiki, Blog]:
        if blogId:
            response = self.get(f"/x{self.comId}/s/blog/{blogId}")
            return Blog(**response.json())

        elif wikiId:
            response = self.get(f"/x{self.comId}/s/item/{wikiId}")
            return Wiki(**response.json())

        elif fileId:
            response = self.get(f"/x{self.comId}/s/shared-folder/files/{fileId}")
            return Wiki(**response.json()["file"])

        else: raise SpecifyType()
    
    def get_blog_comments(self, blogId: str = None, wikiId: str = None, 
            fileId: str = None, sorting: str = "newest", start: int = 0, size: int = 25) -> List[Comment]:
        if blogId:
            url = f"/x{self.comId}/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}"

        elif wikiId:
            url = f"/x{self.comId}/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}"

        elif fileId:
            url = f"/x{self.comId}/s/shared-folder/files/{fileId}/comment?sort={sorting}&start={start}&size={size}"

        else: raise SpecifyType()

        response = self.get(url)
        return list(map(lambda o: Comment(**o), response.json()["commentList"]))
    
    def get_blog_categories(self, size: int = 25) -> List[BlogCategory]:
        response = self.get(f"/x{self.comId}/s/blog-category?size={size}")
        return list(map(lambda o: BlogCategory(**o), response.json()["blogCategoryList"]))

    def get_blogs_by_category(self, categoryId: str, start: int = 0, size: int = 25) -> List[Blog]:
        response = self.get(f"/x{self.comId}/s/blog-category/{categoryId}/blog-list?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response.json()["blogList"]))

    def get_quiz_rankings(self, quizId: str, start: int = 0, size: int = 25)-> QuizRanking:
        response = self.get(f"/x{self.comId}/s/blog/{quizId}/quiz/result?start={start}&size={size}")
        return QuizRanking(**response.json())
    
    def get_wall_comments(self, userId: str, sorting: str, start: int = 0, size: int = 25) -> List[Comment]:
        response = self.get(f"/x{self.comId}/s/user-profile/{userId}/comment?sort={sorting}&start={start}&size={size}")
        return list(map(lambda o: Comment(**o), response.json()["commentList"]))

    def get_recent_blogs(self, pageToken: str = None, start: int = 0, size: int = 25) -> Blog:
        if not pageToken: params = f"v=2&pagingType=t&start={start}&size={size}"
        else: params = f"v=2&pagingType=t&pageToken={pageToken}&start={start}&size={size}"
        
        response = self.get(f"/x{self.comId}/s/feed/blog-all?{params}")
        return list(map(lambda o: Blog(**o, **data["paging"]), (data := response.json())["blogList"]))

    def get_chat_users(self, chatId: str, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2")
        return list(map(lambda o: UserProfile(**o), response.json()["memberList"]))
    
    # TODO : Finish this
    def get_notifications(self, start: int = 0, size: int = 25) -> dict:
        response = self.get(f"/x{self.comId}/s/notification?pagingType=t&start={start}&size={size}")
        return response.json()["notificationList"]
    
    def get_sticker_pack_info(self, sticker_pack_id: str) -> StickerCollection:
        response = self.get(f"/x{self.comId}/s/sticker-collection/{sticker_pack_id}?includeStickers=true")
        return StickerCollection(**response.json()["stickerCollection"])

    def get_sticker_packs(self) -> List[StickerCollection]:
        response = self.get(f"/x{self.comId}/s/sticker-collection?includeStickers=false&type=my-active-collection")
        return list(map(lambda o: StickerCollection(**o), response.json()["stickerCollection"]))

    def get_store_chat_bubbles(self, start: int = 0, size: int = 25) -> List[StoreItem]:
        response = self.get(f"/x{self.comId}/s/store/items?sectionGroupId=chat-bubble&start={start}&size={size}")
        return list(map(lambda o: StoreItem(**o), response.json()["stickerCollection"]))

    def get_store_stickers(self, start: int = 0, size: int = 25) -> List[StoreItem]:
        response = self.get(f"/x{self.comId}/s/store/items?sectionGroupId=sticker&start={start}&size={size}")
        return list(map(lambda o: StoreItem(**o), response.json()["stickerCollection"]))
    
    def get_community_stickers(self) -> List[StickerCollection]:
        response = self.get(f"/x{self.comId}/s/sticker-collection?type=community-shared")
        return list(map(lambda o: StickerCollection(**o), response.json()))

    def get_sticker_collection(self, collectionId: str) -> StickerCollection:
        response = self.get(f"/x{self.comId}/s/sticker-collection/{collectionId}?includeStickers=true")
        return StickerCollection(**response.json()["stickerCollection"])

    # TODO : Finish this
    def get_shared_folder_info(self) -> dict:
        response = self.get(f"/x{self.comId}/s/shared-folder/stats")
        return response.json()["stats"]

    # TODO : Finish this
    def get_shared_folder_files(self, type: str = "latest", start: int = 0, size: int = 25) -> dict:
        response = self.get(f"/x{self.comId}/s/shared-folder/files?type={type}&start={start}&size={size}")
        return response.json()["fileList"]
    
    def reorder_featured_users(self, userIds: list) -> int:
        data = {
            "uidList": userIds
        }

        response = self.post(f"/x{self.comId}/s/user-profile/featured/reorder", data)
        return response.status_code

    def get_hidden_blogs(self, start: int = 0, size: int = 25) -> Blog:
        response = self.get(f"/x{self.comId}/s/feed/blog-disabled?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response.json()["blogList"]))

    def get_featured_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/user-profile?type=featured&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"])) 

    def review_quiz_questions(self, quizId: str) -> List[Blog.QuizQuestion]:
        response = self.get(f"/x{self.comId}/s/blog/{quizId}?action=review")
        return list(map(lambda o: Blog.QuizQuestion(**o), response.json()["blog"]["quizQuestionList"]))

    def get_recent_quiz(self, start: int = 0, size: int = 25) -> Blog:
        response = self.get(f"/x{self.comId}/s/blog?type=quizzes-recent&start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response.json()["blogList"]))

    def get_trending_quiz(self, start: int = 0, size: int = 25) -> Blog:
        response = self.get(f"/x{self.comId}/s/feed/quiz-trending?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response.json()["blogList"]))

    def get_best_quiz(self, start: int = 0, size: int = 25) -> Blog:
        response = self.get(f"/x{self.comId}/s/feed/quiz-best-quizzes?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response.json()["blogList"]))
    
    def moderation_history(self, userId: str = None, blogId: str = None, 
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

        response = self.get(f"/x{self.comId}/s/admin/operation?pagingType=t&size={size}" \
            "?objectId={userId}&objectType={type}" if type and objectId else "")
        return list(map(lambda o: AdminLog(**o), response.json()["adminLogList"]))

    def feature(self, seconds: int, userId: str = None,
            chatId: str = None, blogId: str = None, wikiId: str = None) -> int:
        data = {
            "adminOpName": 114,
            "adminOpValue": {
                "featuredDuration": seconds
            }
        }

        if userId:
            data["adminOpValue"] = {"featuredType": FeaturedTypes.USER}
            response = self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
            return response.status_code

        elif blogId:
            data["adminOpValue"] = {"featuredType": FeaturedTypes.BLOG}
            response = self.post(f"/x{self.comId}/s/blog/{blogId}/admin", data)
            return response.status_code

        elif wikiId:
            data["adminOpValue"] = {"featuredType": FeaturedTypes.WIKI}
            response = self.post(f"/x{self.comId}/s/item/{wikiId}/admin", data)
            return response.status_code

        elif chatId:
            data["adminOpValue"] = {"featuredType": FeaturedTypes.CHAT}
            response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", data)
            return response.status_code

        else: raise SpecifyType()

    def unfeature(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None) -> int:
        data = {
            "adminOpName": 114,
            "adminOpValue": {
                "featuredType": FeaturedTypes.UNFEATURE
            }
        }

        if userId:
            response = self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
            return response.status_code

        elif blogId:
            response = self.post(f"/x{self.comId}/s/blog/{blogId}/admin", data)
            return response.status_code

        elif wikiId:
            response = self.post(f"/x{self.comId}/s/item/{wikiId}/admin", data)
            return response.status_code

        elif chatId:
            response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", data)
            return response.status_code

        else: raise SpecifyType()
    
    def hide(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, reason: str = None) -> int:
        data = {
            "adminOpName": 110,
            "adminOpValue": 9,
            "adminOpNote": {
                "content": reason
            }
        }

        if userId:
            data["adminOpName"] = 18
            response = self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
            return response.status_code

        elif blogId:
            response = self.post(f"/x{self.comId}/s/blog/{blogId}/admin", data)
            return response.status_code

        elif quizId:
            response = self.post(f"/x{self.comId}/s/blog/{quizId}/admin", data)
            return response.status_code

        elif wikiId:
            response = self.post(f"/x{self.comId}/s/item/{wikiId}/admin", data)
            return response.status_code

        elif chatId:
            response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", data)
            return response.status_code

        elif fileId:
            response = self.post(f"/x{self.comId}/s/shared-folder/files/{fileId}/admin", data)
            return response.status_code

        else: raise SpecifyType()

    def unhide(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, reason: str = None) -> int:
        data = {
            "adminOpName": 110,
            "adminOpValue": 0,
            "adminOpNote": {
                "content": reason
            }
        }

        if userId:
            data["adminOpName"] = 19
            response = self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
            return response.status_code

        elif blogId:
            response = self.post(f"/x{self.comId}/s/blog/{blogId}/admin", data)
            return response.status_code

        elif quizId:
            response = self.post(f"/x{self.comId}/s/blog/{quizId}/admin", data)
            return response.status_code

        elif wikiId:
            response = self.post(f"/x{self.comId}/s/item/{wikiId}/admin", data)
            return response.status_code

        elif chatId:
            response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", data)
            return response.status_code

        elif fileId:
            response = self.post(f"/x{self.comId}/s/shared-folder/files/{fileId}/admin", data)
            return response.status_code

        else: raise SpecifyType()

    def edit_titles(self, userId: str, titles: list, colors: list) -> int:
        titles = [{"title": titles, "color": colors} for titles, colors in zip(titles, colors)]

        data = {
            "adminOpName": 207,
            "adminOpValue": {
                "titles": titles
            }
        }

        response = self.post(f"/x{self.comId}/s/user-profile/{userId}/admin", data)
        return response.status_code

    # TODO : List all warning texts
    def warn(self, userId: str, reason: str = None) -> int:
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
            "noticeType": 7
        }

        response = self.post(f"/x{self.comId}/s/notice", data)
        return response.status_code

    # TODO : List all strike texts
    def strike(self, userId: str, seconds: int, title: str = None, reason: str = None) -> int:
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
            "noticeType": 4
        }

        response = self.post(f"/x{self.comId}/s/notice", data)
        return response.status_code
    
    def ban(self, userId: str, reason: str, banType: int = None) -> int:
        data = {
            "reasonType": banType,
            "note": {
                "content": reason
            }
        }

        response = self.post(f"/x{self.comId}/s/user-profile/{userId}/ban", data)
        return response.status_code

    def unban(self, userId: str, reason: str) -> int:
        data = {
            "note": {
                "content": reason
            }
        }

        response = self.post(f"/x{self.comId}/s/user-profile/{userId}/unban", data)
        return response.status_code
    
    def purchase(self, objectId: str, objectType: int, autoRenew: bool = False) -> int:
        data = {
            "v": 1,
            "objectId": objectId,
            "objectType": objectType,
            "paymentContext": {
                "discountStatus": 1, 
                "discountValue": 1, 
                "isAutoRenew": autoRenew
            }
        }

        if self.profile.membershipStatus == 0:
            data["paymentContext"]["discountStatus"] = 0

        response = self.post(f"/x{self.comId}/s/store/purchase", data)
        return response.status_code
    
    def invite_to_vc(self, chatId: str, userId: str) -> int:
        data = {
            "uid": userId
        }

        response = self.post(f"/x{self.comId}/s/chat/thread/{chatId}/vvchat-presenter/invite", data)
        return response.status_code

    def add_poll_option(self, blogId: str, question: str) -> int:
        data = {
            "mediaList": None,
            "title": question,
            "type": 0
        }

        response = self.post(f"/x{self.comId}/s/blog/{blogId}/poll/option", data)
        return response.status_code

    def create_wiki_category(self, title: str, parentCategoryId: str, content: str = None) -> int:
        data = {
            "content": content,
            "icon": None,
            "label": title,
            "mediaList": None,
            "parentCategoryId": parentCategoryId
        }

        response = self.post(f"/x{self.comId}/s/item-category", data)
        return response.status_code

    def create_shared_folder(self, title: str) -> int:
        data = {
            "title": title
        }

        response = self.post(f"/x{self.comId}/s/shared-folder/folders", data)
        return response.status_code

    def submit_to_wiki(self, wikiId: str, message: str) -> int:
        data = {
            "message": message,
            "itemId": wikiId
        }

        response = self.post(f"/x{self.comId}/s/knowledge-base-request", data)
        return response.status_code

    def accept_wiki_request(self, requestId: str, destinationCategoryIdList: list) -> int:
        data = {
            "destinationCategoryIdList": destinationCategoryIdList,
            "actionType": "create"
        }

        response = self.post(f"/x{self.comId}/s/knowledge-base-request/{requestId}/approve", data)
        return response.status_code

    def apply_avatar_frame(self, avatarId: str, applyToAll: bool = True) -> int:
        data = {
            "frameId": avatarId,
            "applyToAll": 0
        }

        if applyToAll:
            data["applyToAll"] = 1

        response = self.post(f"/x{self.comId}/s/avatar-frame/apply", data)
        return response.status_code
    
    def apply_chat_bubble(self, bubbleId: str, chatId: str, applyToAll: bool = False) -> int:
        data = {
            "applyToAll": 0,
            "bubbleId": bubbleId,
            "threadId": chatId
        }

        if applyToAll:
            data["applyToAll"] = 1

        response = self.post(f"/x{self.comId}/s/chat/thread/apply-bubble", data)
        return response.status_code

    def reject_wiki_request(self, requestId: str) -> int:
        response = self.post(f"/x{self.comId}/s/knowledge-base-request/{requestId}/reject")
        return response.status_code

    # TODO : Finish this
    def get_wiki_submissions(self, start: int = 0, size: int = 25) -> dict:
        response = self.get(f"/x{self.comId}/s/knowledge-base-request?type=all&start={start}&size={size}")
        return response.json()["knowledgeBaseRequestList"]
    
    # Live Layer (i dont enf this)
    def get_live_layer(self) -> dict:
        response = self.get(f"/x{self.comId}/s/live-layer/homepage?v=2")
        return response.json()["liveLayerList"]
    
    def get_online_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))
    
    def get_online_users_count(self) -> int:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start=0&size=1")
        return response.json()["userProfileCount"]
    
    def get_public_chats(self, start: int = 0, size: int = 25) -> List[Thread]:
        response = self.get(f"/x{self.comId}/s/live-layer/public-chats?start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["threadList"]))
    
    def get_chatting_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-chatting&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))
    
    def get_chatting_users_count(self) -> int:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-chatting&start=0&size=1")
        return response.json()["userProfileCount"]

    def get_live_chats(self, start: int = 0, size: int = 25) -> List[Thread]:
        response = self.get(f"/x{self.comId}/s/live-layer/public-live-chats?start={start}&size={size}")
        return list(map(lambda o: Thread(**o), response.json()["threadList"]))
    
    def get_live_chatting_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-live-chatting&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))
    
    def get_live_chatting_users_count(self) -> int:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-live-chatting&start=0&size=1")
        return response.json()["userProfileCount"]

    def get_playing_quizzes(self, start: int = 0, size: int = 25) -> List[Blog]:
        response = self.get(f"/x{self.comId}/s/live-layer/quizzes?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response.json()["blogList"]))
    
    def get_playing_quizzes_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-playing-quizzes&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))
    
    def get_playing_quizzes_users_count(self) -> int:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-playing-quizzes&start=0&size=1")
        return response.json()["userProfileCount"]

    def get_browsing_blogs(self, start: int = 0, size: int = 25) -> List[Blog]:
        response = self.get(f"/x{self.comId}/s/live-layer/blogs?start={start}&size={size}")
        return list(map(lambda o: Blog(**o), response.json()["blogList"]))
    
    def get_browsing_blogs_users(self, start: int = 0, size: int = 25) -> List[UserProfile]:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-browsing-blogs&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))
    
    def get_browsing_blogs_users_count(self) -> int:
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:users-browsing-blogs&start=0&size=1")
        return response.json()["userProfileCount"]

    def get_blog_users(self, blogId: str, start: int = 0, size: int = 25):
        response = self.get(f"/x{self.comId}/s/live-layer?topic=ndtopic%3Ax{self.comId}%3Ausers-browsing-blog-at%3A{blogId}&start={start}&size={size}")
        return list(map(lambda o: UserProfile(**o), response.json()["userProfileList"]))
    
    # Live Layer (i dont enf this)

    def activate_bubble(self, bubbleId: str) -> int:
        response = self.post(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}/activate")
        return response.status_code

    def deactivate_bubble(self, bubbleId: str) -> int:
        response = self.post(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}/deactivate")
        return response.status_code    
    
    def get_chat_bubbles(self, chatId: str, start: int = 25, size: int = 25) -> List[ChatBubble]:
        response = self.get(f"/x{self.comId}/s/chat/chat-bubble?type=all-my-bubbles?threadId={chatId}?start={start}?size={size}")
        return list(map(lambda o: ChatBubble(**o), response.json()["chatBubbleList"]))
    
    def get_chat_bubble(self, bubbleId: str) -> ChatBubble:
        response = self.get(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}")
        return ChatBubble(**response.json()["chatBubble"])

    def get_chat_bubble_templates(self, start: int = 0, size: int = 25) -> List[ChatBubble]:
        response = self.get(f"/x{self.comId}/s/chat/chat-bubble/templates?start={start}&size={size}")
        return list(map(lambda o: ChatBubble(**o), response.json()["templateList"]))
    
    def generate_chat_bubble(self, bubble: bytes = None, 
            templateId: str = "949156e1-cc43-49f0-b9cf-3bbbb606ad6e") -> ChatBubble:
        response = self.post(f"/x{self.comId}/s/chat/chat-bubble/templates/{templateId}/generate", data=bubble, type=FileTypes.STREAM)
        return ChatBubble(**response.json()["chatBubble"])
    
    def edit_chat_bubble(self, bubbleId: str, bubble: bytes) -> ChatBubble:
        response = self.post(f"/x{self.comId}/s/chat/chat-bubble/{bubbleId}", data=bubble, type=FileTypes.STREAM)
        return ChatBubble(**response.json()["chatBubble"])

    def send_active_object(self, timers: List[dict], timezone: int = 0, flags: int = 0):
        data = {
            "userActiveTimeChunkList": timers, 
            "optInAdsFlags": flags, 
            "timezone": timezone
        }

        data = json_minify(dumps(data))
        response = self.post(f"/x{self.comId}/s/community/stats/user-active-time", data=data)
        return response.status_code


class CallTypes:
    NONE: int =        0
    VOICE: int =       1
    VIDEO: int =       2
    AVATAR: int =      3
    SCREEN_ROOM: int = 4

class GenderTypes:
    MALE: int =   1
    FAMALE: int = 2
    NONE: int =   255

class CallPermissionTypes:
    OPEN_TO_EVERYONE: int = 1
    JOIN_REQUEST: int =     2
    INVITE_ONLY: int =      3

class FlagTypes:
    AGGRESSION: int =  0
    SPAM: int =        2
    OFFTOPIC: int =    4
    VIOLENCE: int =    106
    INTOLERANCE: int = 107
    SUICIDE: int =     108
    TROLLING: int =    109
    PORNOGRAPHY: int = 110

class FileTypes:
    AUDIO: str =  "audio/aac"
    IMAGE: str =  "image/jpg"
    STREAM: str = "application/octet-stream"

class SortingTypes:
    NEWEST: str = "newest"
    OLDEST: str = "oldest"
    TOP: str =    "vote"

class RepairTypes:
    COINS: str =      "1"
    MEMBERSHIP: str = "2"

class ActivityStatusTypes:
    ON: int =  1
    OFF: int = 2

class ChatPublishTypes:
    IS_GLOBAL: int = 2
    OFF: int =       0
    ON: int =        1

class SourceTypes:
    USER_PROFILE: str =   "UserProfileView"
    DATAIL_POST: str =    "PostDetailView"
    GLOBAL_COMPOSE: str = "GlobalComposeMenu"

class UserTypes:
    RECENT: str =   "recent"
    BANNED: str =   "banned"
    FEATURED: str = "featured"
    LEADERS: str =  "leaders"
    CURATORS: str = "curators"

class LeadernoardTypes:
    DAY: int =        1
    WEEK: int =       2
    REPUTATION: int = 3
    CHECK_IN: int =   4
    QUIZ: int =       5

class FeaturedTypes:
    UNFEATURE: int = 0
    USER: int =      4
    BLOG: int =      1
    WIKI: int =      1
    CHAT: int =      5

class ObjectTypes:
    USER: int =                   0
    BLOG: int =                   1
    ITEM: int =                   2
    COMMENT: int =                3
    BLOG_CATEGORY: int =          4
    BLOG_CATEGORY_ITEM_TAG: int = 5
    FEATURED_ITEM: int =          6
    CHAT_MESSAGE: int =           7

    REPUTATIONLOG_ITEM: int =     10
    POLL_OPTION: int =            11
    CHAT_THREAD: int =            12
    COMMUNITY: int =              16

    IMAGE: int =                  100
    MUSIC: int =                  101
    VIDEO: int =                  102
    YOUTUBE: int =                103
    SHARED_FOLDER: int =          106
    FOLDER_FILE: int =            109

    VOICE: int =                  110
    MODERATION_TASK: int =        111
    SCREENSHOT: int =             112
    STICKER: int =                113
    STICKER_COLLECTION: int =     114
    PROP: int =                   115
    CHAT_BUBBLE: int =            116
    VIDEO_FILTER: int =           117
    ORDER: int =                  118
    SHARE_REQUEST: int =          119

    VV_CHAT: int =                120
    P2A: int =                    121
    AMINO_VIDEO: int =            123

class MessageTypes:
    GENERAL: int =                             0
    STRIKE: int =                              1
    VOICE: int =                               2
    STICKER: int =                             3
    VIDEO: int =                               4

    SHARE_EXURL: int =                         50
    SHARE_USER: int =                          51

    CALL_NO_ANSWERED: int =                    52
    CALL_CANCELLED: int =                      53
    CALL_DECLINED: int =                       54

    VIDEO_CALL_NO_ANSWERED: int =              55
    VIDEO_CALL_CANCELLED: int =                56
    VIDEO_CALL_DECLINED: int =                 57

    AVATAR_CALL_NO_ANSWERED: int =             58
    AVATAR_CALL_CANCELLED: int =               59
    AVATAR_CALL_DECLINED: int =                60

    DELETED: int =                             100
    MEMBER_JOIN: int =                         101
    MEMBER_QUIT: int =                         102
    PRIVATE_CHAT_INIT: int =                   103
      
    BACKGROUND_CHANGE: int =                   104
    TITLE_CHANGE: int =                        105
    ICON_CHANGE: int =                         106

    START_VOICE_CHAT: int =                    107
    START_VIDEO_CHAT: int =                    108
    START_AVATAR_CHAT: int =                   109

    END_VOICE_CHAT: int =                      110
    END_VIDEO_CHAT: int =                      111
    END_AVATAR_CHAT: int =                     112
    CONTENT_CHANGE: int =                      113

    START_SCREENING_ROOM: int =                114
    END_SCREENING_ROOM: int =                  115

    ORGANIZER_TRANSFERRED: int =               116
    FORCE_REMOVED_FROM_CHAT: int =             117

    CHAT_REMOVED: int =                        118
    DELETED_BY_ADMIN: int =                    119

    SEND_COINS: int =                          120
    PIN_ANNOUNCEMENT: int =                    121

    VV_CHAT_PERMISSION_OPEN_TO_EVERYONE: int = 122
    VV_CHAT_PERMISSION_INVITED: int =          123
    VV_CHAT_PERMISSION_INVITE_ONLY: int =      124
    
    ENABALE_VIEW_ONLY: int =                   125
    DISABALE_VIEW_ONLY: int =                  126
    UNPIN_ANNOUNCEMENT: int =                  127
    ENABLE_TIP_PERMISSION: int =               128
    DISABLE_TIP_PERMISSION: int =              129
    
    TIMESTAMP: int =                           65281
    WELCOME_MESSAGE: int =                     65282
    INVITE_MESSAGE: int =                      65283


def all(self: classmethod):
    normal_values: list = []
    values: tuple = self.__dict__.items()
    normal_values.extend([value[1] for value in values if isinstance(value[1], int)])
    return normal_values

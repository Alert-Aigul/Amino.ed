import sys

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union, Dict


class RestrictionInfo(BaseModel):
    discountStatus:    Optional[int]
    ownerUid:          Optional[str]
    ownerType:         Optional[int]
    restrictType:      Optional[int]
    restrictValue:     Optional[int]
    availableDuration: Optional[int]
    discountValue:     Optional[int]


class AvatarFrame(BaseModel):
    class Config(BaseModel):
        name:                Optional[str]
        version:             Optional[int]
        userIconBorderColor: Optional[str]
        avatarFramePath:     Optional[str]
        id:                  Optional[str]
        moodColor:           Optional[str]

    class OwnershipInfo(BaseModel):
        isAutoRenew:     Optional[bool]
        expiredTime:     Optional[str]
        createdTime:     Optional[str]
        ownershipStatus: Optional[int]

    restrictionInfo:     Optional[RestrictionInfo]
    frameUrl:            Optional[str]
    icon:                Optional[str]
    frameId:             Optional[str]
    ownershipStatus:     Optional[int]
    extensions:          Optional[Dict]
    uid:                 Optional[str]
    version:             Optional[int]
    isGloballyAvailable: Optional[bool]
    ownershipInfo:       Optional[OwnershipInfo]
    frameType:           Optional[int]
    md5:                 Optional[str]
    config:              Optional[Config]
    status:              Optional[int]
    name:                Optional[str]
    availableNdcIds:     Optional[List[int]]
    modifiedTime:        Optional[str]
    createdTime:         Optional[str]
    isNew:               Optional[bool]
    resourceUrl:         Optional[str]


class Account(BaseModel):
    class Extensions(BaseModel):
        class DeviceInfo(BaseModel):
            lastClientType: Optional[int]

        deviceInfo:      Optional[DeviceInfo]
        popupConfig:     Optional[Dict]
        contentLanguage: Optional[str]
        adsFlags:        Optional[str]
        adsLevel:        Optional[int]
        avatarFrameId:   Optional[str]
        adsEnabled:      Optional[bool]

    class AdvancedSettings(BaseModel):
        analyticsEnabled: Optional[int]

    extensions:            Optional[Extensions]
    advancedSettings:      Optional[AdvancedSettings]
    username:              Optional[str]
    status:                Optional[int]
    uid:                   Optional[str]
    modifiedTime:          Optional[str]
    twitterID:             Optional[Any]
    activation:            Optional[int]
    phoneNumberActivation: Optional[int]
    emailActivation:       Optional[int]
    appleID:               Optional[Any]
    facebookID:            Optional[Any]
    nickname:              Optional[str]
    googleID:              Optional[str]
    icon:                  Optional[str]
    securityLevel:         Optional[str]
    phoneNumber:           Optional[str]
    membership:            Optional[Any]
    role:                  Optional[int]
    aminoIdEditable:       Optional[bool]
    aminoId:               Optional[str]
    createdTime:           Optional[str]
    email:                 Optional[str]


class UserProfile(BaseModel):
    class Settings(BaseModel):
        onlineStatus: Optional[int]

    class Extensions(BaseModel):
        class Style(BaseModel):
            backgroundColor:     Optional[str]
            backgroundMediaList: Optional[List[List]]
            
        class Title(BaseModel):
            color: Optional[str]
            title: Optional[str]

        style:              Optional[Style]
        __disabledStatus__: Optional[int]
        __disabledTime__:   Optional[int]
        __disabledLevel__:  Optional[int]
        hideUserProfile:    Optional[bool]
        defaultBubbleId:    Optional[str]

        customTitles:                    Optional[List[Title]]
        coverAnimation:                  Optional[Any]
        isMemberOfTeamAmino:             Optional[bool]
        privilegeOfChatInviteRequest:    Optional[int]
        privilegeOfCommentOnUserProfile: Optional[int]

    class InfluencerInfo(BaseModel):
        fansCount:   Optional[int]
        monthlyFee:  Optional[int]
        pinned:      Optional[bool]
        createdTime: Optional[str]
        
    extensions:              Optional[Extensions]
    influencerInfo:          Optional[InfluencerInfo]
    avatarFrame:             Optional[AvatarFrame]
    settings:                Optional[Settings]
    status:                  Optional[int]
    moodSticker:             Optional[Any]
    itemsCount:              Optional[int]
    consecutiveCheckInDays:  Optional[str]
    uid:                     Optional[str]
    modifiedTime:            Optional[str]
    followingStatus:         Optional[int]
    onlineStatus:            Optional[int]
    accountMembershipStatus: Optional[int]
    isGlobal:                Optional[bool]
    avatarFrameId:           Optional[str]
    reputation:              Optional[int]
    postsCount:              Optional[int]
    followersCount:          Optional[int]
    nickname:                Optional[str]
    icon:                    Optional[str]
    isVerified:              Optional[bool]
    visitorsCount:           Optional[int]
    mood:                    Optional[Any]
    level:                   Optional[int]
    pushEnabled:             Optional[bool]
    membershipStatus:        Optional[int]
    content:                 Optional[str]
    followedCount:           Optional[int]
    role:                    Optional[int]
    commentsCount:           Optional[int]
    aminoId:                 Optional[str]
    ndcId:                   Optional[int]
    createdTime:             Optional[str]
    visitPrivacy:            Optional[int]
    storiesCount:            Optional[int]
    blogsCount:              Optional[int]


class Auth(BaseModel):
    auid:     Optional[str]
    account:  Optional[Account]
    sid:      Optional[str]
    secret:   Optional[str]
    user:     Optional[UserProfile] = Field(alias="userProfile")
    deviceId: Optional[str]


class Community(BaseModel):
    class AdvancedSettings(BaseModel):
        class RankingTableItem(BaseModel):
            title:      Optional[str]
            level:      Optional[int]
            reputation: Optional[int]
            id:         Optional[int]

        class NewsFeedPage(BaseModel):
            status: Optional[int]
            type:   Optional[int]

        rankingTable:                    Optional[List[RankingTableItem]]
        frontPageLayout:                 Optional[int]
        leaderboardStyle:                Optional[Dict]
        newsfeedPages:                   Optional[List[NewsFeedPage]]
        facebookAppIdList:               Optional[Any]
        hasPendingReviewRequest:         Optional[bool]
        joinedBaselineCollectionIdList:  Optional[List]
        defaultRankingTypeInLeaderboard: Optional[int]
        welcomeMessageText:              Optional[Any]
        pollMinFullBarVoteCount:         Optional[int]
        welcomeMessageEnabled:           Optional[Any]
        catalogEnabled:                  Optional[bool]

    class UserAddedTopic(BaseModel):
        class Style(BaseModel):
            backgroundColor: Optional[str]

        style:   Optional[Style]
        topicId: Optional[int]
        name:    Optional[str]

    class ThemePack(BaseModel):
        themePackHash:     Optional[str]
        themePackRevision: Optional[int]
        themePackUrl:      Optional[str]
        themeColor:        Optional[str]

    class Configuration(BaseModel):
        class Module(BaseModel):
            class Ranking(BaseModel):
                class Leaderboard(BaseModel):
                    type:    Optional[int]
                    id:      Optional[int]
                    enabled: Optional[bool]

                class Table(BaseModel):
                    id: Optional[int]
                    title:      Optional[str]
                    level:      Optional[int]
                    reputation: Optional[int]

                enabled:                Optional[bool]
                leaderboardList:        Optional[List[Leaderboard]]
                leaderboardEnabled:     Optional[bool]
                rankingTable:           Optional[List[Table]]
                defaultLeaderboardType: Optional[int]

            class Chat(BaseModel):
                class AvChat(BaseModel):
                    audioEnabled:         Optional[bool]
                    videoEnabled:         Optional[bool]
                    audio2Enabled:        Optional[bool]
                    screeningRoomEnabled: Optional[bool]

                class PublicChat(BaseModel):
                    class Privilege(BaseModel):
                        type:     Optional[int]
                        minLevel: Optional[int]

                    privilege: Optional[Privilege]
                    enabled:   Optional[bool]

                avChat:                Optional[AvChat]
                publicChat:            Optional[PublicChat]
                spamProtectionEnabled: Optional[bool]
                enabled:               Optional[bool]

            class ExternalContent(BaseModel):
                enabled: Optional[bool]

            class Post(BaseModel):
                class PostType(BaseModel):
                    class Type(BaseModel):
                        class Privilege(BaseModel):
                            type:     Optional[int]
                            minLevel: int = 0

                        privilege: Optional[Privilege]
                        enabled:   Optional[bool]

                    image:           Optional[Type]
                    quiz:            Optional[Type]
                    question:        Optional[Type]
                    blog:            Optional[Type]
                    publicChatRooms: Optional[Type]
                    poll:            Optional[Type]
                    screeningRoom:   Optional[Type]
                    catalogEntry:    Optional[Type]
                    story:           Optional[Type]
                    liveMode:        Optional[Type]
                    webLink:         Optional[Type]

                postType: Optional[PostType]
                enabled:  Optional[bool]

            class Influencer(BaseModel):
                enabled:          Optional[bool]
                maxVipMonthlyFee: Optional[int]
                minVipMonthlyFee: Optional[int]
                lock:             Optional[bool]
                maxVipNumbers:    Optional[int]

            class Catalog(BaseModel):
                class Privilege(BaseModel):
                    type: Optional[int]

                privilege:       Optional[Privilege]
                enabled:         Optional[bool]
                curationEnabled: Optional[bool]

            class SharedFolder(BaseModel):
                class AlbumManagePrivilege(BaseModel):
                    type:     Optional[int]
                    minLevel: Optional[int]

                class UploadPrivilege(BaseModel):
                    minLevel: Optional[int]
                    type:     Optional[int]

                uploadPrivilege:      Optional[UploadPrivilege]
                albumManagePrivilege: Optional[AlbumManagePrivilege]
                enabled:              Optional[bool]

            class Featured(BaseModel):
                enabled:               Optional[bool]
                lockMember:            Optional[bool]
                postEnabled:           Optional[bool]
                layout:                Optional[int]
                publicChatRoomEnabled: Optional[bool]
                memberEnabled:         Optional[bool]

            ranking: Optional[Ranking]
            chat:            Optional[Chat]
            externalContent: Optional[ExternalContent]
            post:            Optional[Post]
            influencer:      Optional[Influencer]
            catalog:         Optional[Catalog]
            sharedFolder:    Optional[SharedFolder]
            featured:        Optional[Featured]

        class General(BaseModel):
            class WelcomeMessage(BaseModel):
                enabled: Optional[bool]
                text:    Optional[str]

            welcomeMessage:                 Optional[WelcomeMessage]
            disableLiveLayerVisible:        Optional[bool]
            joinedTopicIdList:              Optional[List[int]]
            disableLocation:                Optional[bool]
            premiumFeatureEnabled:          Optional[bool]
            onlyAllowOfficialTag:           Optional[bool]
            videoUploadPolicy:              Optional[int]
            accountMembershipEnabled:       Optional[bool]
            joinedBaselineCollectionIdList: Optional[List]
            invitePermission:               Optional[int]
            hasPendingReviewRequest:        Optional[bool]
            disableLiveLayerActive:         Optional[bool]
            facebookAppIdList:              Optional[Any]

        class Appearance(BaseModel):
            class HomePage(BaseModel):
                class IdObj(BaseModel):
                    id: Optional[str]

                navigation: Optional[List[IdObj]]

            class LeftSidePanel(BaseModel):
                class Navigation(BaseModel):
                    class IdObj(BaseModel):
                        id: Optional[str]

                    level2: Optional[List[IdObj]]
                    level1: Optional[List[IdObj]]

                class Style(BaseModel):
                    iconColor: Optional[str]

                navigation: Optional[Navigation]
                style:      Optional[Style]

            homePage:      Optional[HomePage]
            leftSidePanel: Optional[LeftSidePanel]

        class Page(BaseModel):
            class DefaultObject(BaseModel):
                url:   Optional[str]
                alias: Optional[Any]
                id:    Optional[str]

            defaultList: Optional[List[DefaultObject]]
            customList:  Optional[List]

        module:     Optional[Module]
        appearance: Optional[Appearance]
        general:    Optional[General]
        page:       Optional[Page]

    icon:                               Optional[str]
    configuration:                      Optional[Configuration]
    communityHeadList:                  Optional[List[UserProfile]]
    status:                             Optional[int]
    probationStatus:                    Optional[int]
    influencerList:                     Optional[List[UserProfile]]
    ListedStatus:                       Optional[int]
    advancedSettings:                   Optional[AdvancedSettings]
    searchable:                         Optional[bool]
    communityHeat:                      Optional[int]
    endpoint:                           Optional[str]
    joinType:                           Optional[int]
    modifiedTime:                       Optional[str]
    userAddedTopicList:                 Optional[List[UserAddedTopic]]
    content:                            Optional[Any]
    ndcId:                              Optional[int]
    mediaList:                          Optional[Any]
    primaryLanguage:                    Optional[str]
    keywords:                           Optional[str]
    name:                               Optional[str]
    membersCount:                       Optional[int]
    isStandaloneAppDeprecated:          Optional[bool]
    isStandaloneAppMonetizationEnabled: Optional[bool]
    link:                               Optional[str]
    agent:                              Optional[UserProfile]
    themePack:                          Optional[ThemePack]
    activeInfo:                         Optional[Dict]
    templateId:                         Optional[int]
    tagline:                            Optional[str]
    createdTime:                        Optional[str]
    extensions:                         Optional[Any]
    promotionalMediaList:               Optional[List[List]]


class ChatBubble(BaseModel):
    class Config(BaseModel):
        status:               Optional[int]
        allowedSlots:         Optional[List[Dict]]
        name:                 Optional[str]
        contentInsets:        Optional[List[int]]
        zoomPoint:            Optional[List[int]]
        version:              Optional[int]
        linkColor:            Optional[str]
        slots:                Optional[List[Dict]]
        backgroundPath:       Optional[str]
        id:                   Optional[str]
        color:                Optional[str]
        previewBackgroundUrl: Optional[str]
        coverImage:           Optional[str]

    config:          Optional[Config]
    status:          Optional[int]
    resourceUrl:     Optional[str]
    name:            Optional[str]
    modifiedTime:    Optional[str]
    uid:             Optional[str]
    restrictionInfo: Optional[Any]
    coverImage:      Optional[str]
    isNew:           Optional[bool]
    bubbleType:      Optional[int]
    ownershipStatus: Optional[int]
    version:         Optional[int]
    backgroundImage: Optional[str]
    extensions:      Optional[Dict]
    deletable:       Optional[bool]
    templateId:      Optional[str]
    createdTime:     Optional[str]
    bubbleId:        Optional[str]
    bannerImage:     Optional[str]
    md5:             Optional[str]


class TipInfo(BaseModel):
    class TipOption(BaseModel):
        value: Optional[int]
        icon:  Optional[str]

    tipCustomOption: Optional[TipOption]
    tipOptionList:   Optional[List[TipOption]]
    tipMaxCoin:      Optional[int]
    tippersCount:    Optional[int]
    tippable:        Optional[bool]
    tipMinCoin:      Optional[int]
    tippedCoins:     Optional[float]


class Thread(BaseModel):
    class Topic(BaseModel):
        class Style(BaseModel):
            backgroundColor: Optional[str]

        status:                  Optional[int]
        isOfficial:              Optional[bool]
        style:                   Optional[Style]
        isAlias:                 Optional[bool]
        name:                    Optional[str]
        contentPoolId:           Optional[str]
        subTopicList:            Optional[List]
        coverImage:              Optional[str]
        aliasTopicList:          Optional[List]
        advancedCommunityStatus: Optional[int]
        increaseId:              Optional[int]
        visibility:              Optional[int]
        source:                  Optional[int]
        chatStatus:              Optional[int]
        topicId:                 Optional[int]
        storyId:                 Optional[str]
        scope:                   Optional[int]
        advancedStatus:          Optional[int]
        isLocked:                Optional[bool]
        tabList:                 Optional[List]
        objectMappingScore:      Optional[int]

    class Member(BaseModel):
        status:           Optional[int]
        uid:              Optional[str]
        membershipStatus: Optional[int]
        role:             Optional[int]
        nickname:         Optional[str]
        icon:             Optional[str]

    class LastMessage(BaseModel):
        uid:         Optional[str]
        type:        Optional[int]
        mediaType:   Optional[int]
        content:     Optional[str]
        messageId:   Optional[str]
        createdTime: Optional[str]
        isHidden:    Optional[bool]
        mediaValue:  Optional[Any]

    class Extensions(BaseModel):
        class ScreeningRoomPermission(BaseModel):
            action:  Optional[int]
            uidList: Optional[List]

        screeningRoomPermission:      Optional[ScreeningRoomPermission]
        viewOnly:                     Optional[bool]
        coHost:                       Optional[List[str]]
        language:                     Optional[str]
        membersCanInvite:             Optional[bool]
        bm:                           Optional[List]
        creatorUid:                   Optional[str] = Field(alias="uid")
        visibility:                   Optional[int]
        bannedMemberUidList:          Optional[List[str]]
        lastMembersSummaryUpstr: Optional[int]
        fansOnly:                     Optional[bool]
        announcement:                 Optional[str]
        channelType:                  Optional[int]
        pinAnnouncement:              Optional[bool]
        vvChatJoinType:               Optional[int]

    author:             Optional[UserProfile]
    extensions:         Optional[Extensions]
    lastMessageSummary: Optional[LastMessage]
    tipInfo:            Optional[TipInfo]
    userAddedTopicList: Optional[Topic]
    uid:                Optional[str]
    membersSummary:     Optional[List[Member]]
    membersQuota:       Optional[int]
    threadId:           Optional[str]
    keywords:           Optional[str]
    membersCount:       Optional[int]
    strategyInfo:       Optional[Any]
    isPinned:           Optional[bool]
    title:              Optional[str]
    membershipStatus:   Optional[int]
    content:            Optional[str]
    needHidden:         Optional[bool]
    alertOption:        Optional[int]
    lastReadTime:       Optional[str]
    type:               Optional[int]
    status:             Optional[int]
    publishToGlobal:    Optional[int]
    modifiedTime:       Optional[str]
    condition:          Optional[int]
    icon:               Optional[str]
    latestActivityTime: Optional[str]
    ndcId:              Optional[int]
    createdTime:        Optional[str]
    chatBubbles:        Optional[Dict[str, ChatBubble]]


class Sticker(BaseModel):
    status:              Optional[int]
    iconV2:              Optional[str]
    name:                Optional[str]
    stickerId:           Optional[str]
    smallIconV2:         Optional[Any]
    smallIcon:           Optional[Any]
    stickerCollectionId: Optional[Any]
    mediumIcon:          Optional[Any]
    extensions:          Optional[Dict]
    usedCount:           Optional[int]
    mediumIconV2:        Optional[Any]
    createdTime:         Optional[str]
    icon:                Optional[str]


class Message(BaseModel):
    class Extensions(BaseModel):
        class Mention(BaseModel):
            uid: str

        sticker:           Optional[Sticker]
        originalStickerId: Optional[str]
        mentionedArray:    Optional[List[Mention]]
        replyMessage:      Optional[Dict]
        replyMessageId:    Optional[str]

    extensions:        Optional[Extensions]
    includedInSummary: Optional[bool]
    author:            Optional[UserProfile]
    isHidden:          Optional[bool]
    chatBubble:        Optional[ChatBubble]
    messageId:         Optional[str]
    mediaType:         Optional[int]
    content:           Optional[str]
    chatBubbleId:      Optional[str]
    clientRefId:       Optional[int]
    threadId:          Optional[str]
    createdTime:       Optional[str]
    chatBubbleVersion: Optional[int]
    type:              Optional[int]
    uid:               Optional[str]
    mediaValue:        Optional[str]
    nextPageToken:     Optional[str]
    prevPageToken:     Optional[str]

    @property
    def replies(self) -> 'Message':
        Message: 'Message' = getattr(sys.modules[__name__], 'Message')

        return Message(**(self.extensions.replyMessage or {
            "author": {}, "extensions": {"sticker": {}}, "chatBubble": {}}))


class Blog(BaseModel):
    class QuizQuestion(BaseModel):
        class Extensions(BaseModel):
            class QuestionOpt(BaseModel):
                optId: Optional[str]
                qhash: Optional[str]
                title: Optional[str]

            quizQuestionOptList: Optional[List[QuestionOpt]]
            __disabledLevel__: Optional[int]

        status:         Optional[int]
        parentType:     Optional[int]
        extensions:     Optional[Extensions]
        title:          Optional[str]
        createdTime:    Optional[str]
        quizQuestionId: Optional[str]
        parentId:       Optional[str]
        mediaList:      Optional[List[List]]

    class Extensions(BaseModel):
        class Style(BaseModel):
            coverMediaIndexList: Optional[Any]
            backgroundMediaList: Optional[List[List]]

        style:                   Optional[Style]
        quizPlayedTimes:         Optional[int]
        quizTotalQuestionCount:  Optional[int]
        quizTrendingTimes:       Optional[int]
        quizLastAddQuestionTime: Optional[int]
        fansOnly:                Optional[bool]

    globalVotesCount:      Optional[int]
    globalVotedValue:      Optional[int]
    votedValue:            Optional[int]
    keywords:              Optional[str]
    mediaList:             Optional[List[List]]
    style:                 Optional[int]
    totalQuizPlayCount:    Optional[int]
    title:                 Optional[str]
    tipInfo:               Optional[TipInfo]
    contentRating:         Optional[int]
    content:               Optional[str]
    needHidden:            Optional[bool]
    guestVotesCount:       Optional[int]
    type:                  Optional[int]
    status:                Optional[int]
    globalCommentsCount:   Optional[int]
    modifiedTime:          Optional[str]
    quizQuestionList:      Optional[List[QuizQuestion]]
    widgetDisplayInterval: Optional[Any]
    totalPollVoteCount:    Optional[int]
    blogId:                Optional[str]
    viewCount:             Optional[int]
    language:              Optional[str]
    author:                Optional[UserProfile]
    extensions:            Optional[Extensions]
    votesCount:            Optional[int]
    ndcId:                 Optional[int]
    createdTime:           Optional[str]
    endTime:               Optional[Any]
    commentsCount:         Optional[int]
    nextPageToken:         Optional[str]
    prevPageToken:         Optional[str]


class Wiki(BaseModel):
    class Extensions(BaseModel):
        fansOnly: Optional[bool]

    globalVotesCount:    Optional[int]
    globalVotedValue:    Optional[int]
    votedValue:          Optional[int]
    keywords:            Optional[str]
    mediaList:           Optional[List[List]]
    style:               Optional[int]
    author:              Optional[UserProfile]
    tipInfo:             Optional[TipInfo]
    contentRating:       Optional[int]
    label:               Optional[str]
    content:             Optional[str]
    needHidden:          Optional[bool]
    guestVotesCount:     Optional[int]
    status:              Optional[int]
    globalCommentsCount: Optional[int]
    modifiedTime:        Optional[str]
    itemId:              Optional[str]
    extensions:          Optional[Extensions]
    votesCount:          Optional[int]
    ndcId:               Optional[int]
    createdTime:         Optional[str]
    commentsCount:       Optional[int]


class Comment(BaseModel):
    modifiedTime:     Optional[str]
    ndcId:            Optional[int]
    votedValue:       Optional[int]
    parentType:       Optional[int]
    commentId:        Optional[str]
    parentNdcId:      Optional[int]
    mediaList:        Optional[List[List]]
    votesSum:         Optional[int]
    author:           Optional[UserProfile]
    content:          Optional[str]
    extensions:       Optional[Dict]
    parentId:         Optional[str]
    createdTime:      Optional[str]
    subcommentsCount: Optional[int]
    type:             Optional[int]


class Link(BaseModel):
    objectId:   Optional[str]
    targetCode: Optional[int]
    ndcId:      Optional[int]
    fullPath:   Optional[str]
    shortCode:  Optional[str]
    objectType: Optional[int]
    community:  Optional[Community]


class Wallet(BaseModel):
    class AdsVideoStats(BaseModel):
        watchVideoMaxCount:     Optional[int]
        nextWatchVideoInterval: Optional[float]
        watchedVideoCount:      Optional[int]
        canWatchVideo:          Optional[bool]
        canEarnedCoins:         Optional[int]
        canNotWatchVideoReason: Optional[str]

    adsVideoStats:           Optional[AdsVideoStats]
    totalBusinessCoins:      Optional[int]
    totalBusinessCoinsFloat: Optional[float]
    totalCoinsFloat:         Optional[float]
    adsEnabled:              Optional[bool]
    adsFlags:                Optional[int]
    totalCoins:              Optional[int]
    businessCoinsEnabled:    Optional[bool]


class Transaction(BaseModel):
    class ExtData(BaseModel):
        icon: Optional[str]
        subtitle: Optional[str]
        objectDeeplinkUrl: Optional[str]
        description: Optional[str]

    extData:           Optional[ExtData]
    uid:               Optional[str]
    totalCoins:        Optional[int]
    originCoins:       Optional[int]
    bonusCoins:        Optional[int]
    changedCoins:      Optional[int]
    taxCoins:          Optional[int]
    sourceType:        Optional[int]
    taxCoinsFloat:     Optional[float]
    bonusCoinsFloat:   Optional[float]
    totalCoinsFloat:   Optional[float]
    createdTime:       Optional[str]
    changedCoinsFloat: Optional[float]
    isPositive:        Optional[bool]
    originCoinsFloat:  Optional[float]


class Membership(BaseModel):
    uid:              Optional[str]
    paymentType:      Optional[int]
    expiredTime:      Optional[str]
    renewedTime:      Optional[str]
    modifiedTime:     Optional[str]
    createdTime:      Optional[str]
    isAutoRenew:      Optional[bool]
    membershipStatus: Optional[int]


class InviteCode(BaseModel):
    status:       Optional[int]
    duration:     Optional[int]
    invitationId: Optional[str]
    link:         Optional[str]
    modifiedTime: Optional[str]
    ndcId:        Optional[int]
    createdTime:  Optional[str]
    inviteCode:   Optional[str]


class StickerCollection(BaseModel):
    class Extensions(BaseModel):
        class OriginalCommunity(BaseModel):
            status:   Optional[int]
            icon:     Optional[str]
            endpoint: Optional[str]
            name:     Optional[str]
            ndcId:    Optional[int]

        iconSourceStickerId: Optional[str]
        originalAuthor:      Optional[UserProfile]
        originalCommunity:   Optional[OriginalCommunity]

    status:              Optional[int]
    isActivated:         Optional[bool]
    collectionType:      Optional[int]
    uid:                 Optional[str]
    modifiedTime:        Optional[str]
    isNew:               Optional[bool]
    bannerUrl:           Optional[str]
    smallIcon:           Optional[str]
    stickersCount:       Optional[int]
    ownershipStatus:     Optional[Any]
    usedCount:           Optional[int]
    availableNdcIds:     Optional[List]
    icon:                Optional[str]
    name:                Optional[str]
    collectionId:        Optional[str]
    description:         Optional[str]
    author:              Optional[UserProfile]
    extensions:          Optional[Extensions]
    createdTime:         Optional[str]
    isGloballyAvailable: Optional[bool]
    restrictionInfo:     Optional[RestrictionInfo]


class Lottery(BaseModel):
    class LotteryLog(BaseModel):
        awardValue:  Optional[int]
        parentType:  Optional[int]
        objectId:    Optional[str]
        parentId:    Optional[str]
        createdTime: Optional[str]
        awardType:   Optional[int]
        refObject:   Optional[Dict]
        objectType:  Optional[int]

    wallet:     Optional[Wallet]
    lotteryLog: Optional[LotteryLog]


class Achievement(BaseModel):
    secondsSpentOfLast24Hours: Optional[float]
    secondsSpentOfLast7Days:   Optional[float]
    numberOfMembersCount:      Optional[int]
    numberOfPostsCreated:      Optional[int]


class CheckIn(BaseModel):
    class CheckInHistory(BaseModel):
        joinedTime:             Optional[int]
        stopTime:               Optional[int]
        consecutiveCheckInDays: Optional[int]
        streakRepairCoinCost:   Optional[int]
        startTime:              Optional[int]
        hasCheckInToday:        Optional[bool]
        streakRepairWindowSize: Optional[int]
        hasAnyCheckIn:          Optional[bool]
        history:                Optional[str]

    consecutiveCheckInDays:    Optional[int]
    canPlayLottery:            Optional[bool]
    earnedReputationPoint:     Optional[int]
    additionalReputationPoint: Optional[int]
    checkInHistory:            Optional[CheckInHistory]
    userProfile:               Optional[UserProfile]


class TippedUserSummary(BaseModel):
    tipper:           Optional[UserProfile]
    lastTippedTime:   Optional[str]
    totalTippedCoins: Optional[float]
    lastThankedTime:  Optional[str]


class Bookmark(BaseModel):
    refObjectType:  Optional[int]
    bookmarkedTime: Optional[str]
    refObjectId:    Optional[str]
    refObject:      Optional[Union[Blog, Wiki]]


class QuizRanking(BaseModel):
    highestMode:    Optional[int]
    modifiedTime:   Optional[str]
    isFinished:     Optional[bool]
    hellIsFinished: Optional[bool]
    highestScore:   Optional[int]
    beatRate:       Optional[Any]
    lastBeatRate:   Optional[Any]
    totalTimes:     Optional[int]
    latestScore:    Optional[int]
    author:         Optional[UserProfile]


class BlogCategory(BaseModel):
    blogsCount:   Optional[int]
    status:       Optional[int]
    type:         Optional[int]
    modifiedTime: Optional[str]
    label:        Optional[str]
    style:        Optional[int]
    categoryId:   Optional[str]
    createdTime:  Optional[str]
    position:     Optional[int]
    icon:         Optional[str]
    content:      Optional[str]


class VcReputation(BaseModel):
    participantCount: Optional[int]
    totalReputation:  Optional[int]
    duration:         Optional[int]


class AdminLog(BaseModel):
    class Author(BaseModel):
        icon:     Optional[str]
        status:   Optional[int]
        role:     Optional[int]
        nickname: Optional[str]
        uid:      Optional[str]
    
    objectUrl:       Optional[str]
    operationName:   Optional[str]
    createdTime:     Optional[str]
    referTicketId:   Optional[str]
    extData:         Optional[Dict]
    objectId:        Optional[str]
    moderationLevel: Optional[int]
    refObject:       Optional[Dict]
    author:          Optional[Author]
    objectType:      Optional[int]
    operation:       Optional[int]
    operationDetail: Optional[str]
    ndcId:           Optional[int]
    operationLevel:  Optional[str]
    logId:           Optional[str]


class StoreItem(BaseModel):
    class ItemBasicInfo(BaseModel):
        icon: Optional[str]
        name: Optional[str]

    refObjectType:       Optional[int]
    refObjectId:         Optional[str]
    createdTime:         Optional[str]
    itemBasicInfo:       Optional[ItemBasicInfo]
    itemRestrictionInfo: Optional[RestrictionInfo]
    refObject:           Optional[Union[ChatBubble, AvatarFrame, StickerCollection]]


class StoreSections(BaseModel):
    name:                 Optional[str]
    sectionGroupId:       Optional[str]
    allItemsCount:        Optional[int]
    icon:                 Optional[str]
    storeSectionId:       Optional[str]
    previewStoreItemList: Optional[StoreItem]


class BaseEvent(Message):
    ndcId:            Optional[int]
    alertOption:      Optional[int]
    membershipStatus: Optional[int]
    __warned__:       Optional[bool] # 🤡


class SID(BaseModel):
    signature:  Optional[str]
    prefix:     Optional[str]
    original:   Optional[str]
    data:       Optional[dict]
    version:    Optional[int] = Field(alias="0") # ?
    uid:        Optional[str] = Field(alias="2")
    ip:         Optional[str] = Field(alias="4")
    makeTime:   Optional[int] = Field(alias="5")
    clientType: Optional[int] = Field(alias="6")

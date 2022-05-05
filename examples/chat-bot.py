import aminoed


client = aminoed.Client()

@client.execute()
async def on_start():
    communities = await client.get_account_communities(0, 100)
    print(f"Bot {client.profile.nickname} started on {len(communities)} communities.")

@client.on(aminoed.EventTypes.MESSAGE)
async def on_message(event: aminoed.Event):
    content = event.message.content
    chatId = event.message.chatId
    messageId = event.message.messageId
    
    nickname = event.message.author.nickname
    community = await client.community(event.comId)
    
    print(f"{nickname}: {content}")
    
    if content.startswith("!ping"):
        await community.send_message(chatId, "pong!", replyTo=messageId)
        
    elif content.startswith("!chatid"):
        await community.send_message(chatId, chatId, replyTo=messageId)

client.start("email", "password")

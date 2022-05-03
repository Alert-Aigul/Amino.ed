import aminoed.sync as aminoed


client = aminoed.Client()

@client.execute()
def on_start():
    communities = client.get_account_communities(0, 100)
    print(f"Bot {client.profile.nickname} started on {len(communities)} communities.")

@client.on("message")
def on_message(event: aminoed.Event):
    content = event.message.content
    chatId = event.message.chatId
    messageId = event.message.messageId
    
    nickname = event.message.author.nickname
    community = client.community(event.comId)
    
    print(f"{nickname}: {content}")
    
    if content.startswith("!ping"):
        community.send_message(chatId, "pong!", replyTo=messageId)
        
    elif content.startswith("!chatid"):
        community.send_message(chatId, chatId, replyTo=messageId)

client.start("email", "password")

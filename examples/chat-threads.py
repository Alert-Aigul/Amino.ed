import aminoed


@aminoed.run_with_client()
async def main(client: aminoed.Client):
    await client.login("email", "password")
    
    chats = await client.get_chat_threads()
    
    for index, chat in enumerate(chats, 1):
        if chat.type == 0:
            print(f"{index}. {chat.title or chat.author.nickname} (DM)")
        elif chat.type == 1:
            print(f"{index}. {chat.title or chat.author.nickname} (Private)")
        elif chat.type == 2:
            print(f"{index}. {chat.title} (Public)")
        else:
            print(f"{index}. {chat.title} (Unknown)")

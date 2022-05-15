from aminoed import *

bot = Client(prefix="!")

@bot.execute()
async def on_start():
    print(f"Bot {bot.auth.user.nickname} working.")
    
@bot.command()
async def help(event: Event):
    await event.send("[c]Comands\n" \
        "?chatmembers - members count.")

@bot.command("1000-7", "")
async def deadinside(event: Event):
    await event.reply("993")

@bot.command("chatmembers", "?")
async def chatmembers(event: Event):
    chat = await event.client.get_chat_thread(event.threadId)
    await event.send(f"Chat members count: {chat.membersCount}.")
    
bot.start("", "")

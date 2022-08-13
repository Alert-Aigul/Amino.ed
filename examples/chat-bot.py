from aminoed import *

bot = Client(prefix="!")

@bot.execute() # Runs in the background, after bot.start()
async def on_start():
    print(f"Bot {bot.auth.user.nickname} working.")
    
@bot.command() # Comand name - function name
async def help(event: Event):
    await event.send_message("[c]Comands\n" \
        "?chatmembers - members count.")
    
@bot.command("1000-7", "")
async def deadinside(event: Event):
    await event.reply_message("993")
    
@bot.command("chatmembers", "?") # Custom command and prefix
async def chatmembers(event: Event):
    chat = await event.client.get_chat_thread(event.threadId)
    await event.send_message(f"Chat members count: {chat.membersCount}.")
    
@bot.on(MessageTypes.GENERAL) # On default message
async def chatmembers(event: Event):
    print(event.author.nickname, event.content)
    
bot.start("email", "password")
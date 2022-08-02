# Installing
```
pip install amino.ed
```

# Example
```py
import aminoed

@aminoed.run_with_client()
async def main(client: aminoed.Client):
    await client.login("email", "password")

```

# Chat-bot example
```py
from aminoed import *

bot = Client(prefix="!")

@bot.execute() # Runs in the background, after bot.start()
async def on_start():
    print(f"Bot {bot.auth.user.nickname} working.")
    
@bot.command() # Comand name - function name
async def help(event: Event):
    await event.send_message("[c]Comands\n" \
        "?chatmembers - members count.")

@bot.command("chatmembers", "?") # Custom command and prefix
async def chatmembers(event: Event):
    chat = await event.client.get_chat_thread(event.threadId)
    await event.send_message(f"Chat members count: {chat.membersCount}.")
    
bot.start("email", "password")


```

import aminoed

@aminoed.run_with_client()
async def main(client: aminoed.Client):
    ip = await client.with_proxy(
        "proxy", # one argument - your proxy 
        client.get_request, # one argument - two atrgument function
        "http://api.ipify.org/" # this and other arguments - client.get_request arguments
    )
    
    print(await ip.text())

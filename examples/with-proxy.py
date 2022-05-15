import aminoed

@aminoed.run_with_client()
async def main(client: aminoed.Client):
    ip = await client.with_proxy(
        "proxy", # one argument - your proxy 
        client.session.request,  # one argument - two atrgument function
        "GET", # this and other arguments - client.session.request arguments
        "http://api.ipify.org/" 
    )
    
    print(await ip.text())

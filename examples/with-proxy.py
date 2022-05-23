import aminoed

@aminoed.run_with_client()
async def main(client: aminoed.Client):
    auth = await client.with_proxy(
        client.login, "proxy")("email", "password")
    
    client.set_auth(auth)
    
    print(aminoed.decode_sid(client.auth.sid).ip)

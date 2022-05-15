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

# Version note
How badly I did it all, I'll fix it in the next updates.

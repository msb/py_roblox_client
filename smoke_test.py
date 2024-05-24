import asyncio
import roblox_client

async def test():
    common = dict(
        headers={'x-api-key': 'xxxxxxxxxxxxxxxxxxxx'}
    )
    async with roblox_client.ods_client('universe_id', 'the-data-store-name', **common) as ods_client:
        await ods_client.delete("this-key-doesnt-exist")

# you should get a 401
asyncio.run(test())

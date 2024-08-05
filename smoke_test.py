import pytest
from aiohttp.client_exceptions import ClientResponseError

import roblox_client


@pytest.mark.asyncio
async def test():
    common = dict(
        headers={'x-api-key': 'xxxxxxxxxxxxxxxxxxxx'}
    )
    async with roblox_client.ods_client('universe_id', 'data-store-name', **common) as ods_client:
        with pytest.raises(ClientResponseError, match='401'):
            await ods_client.delete('this-key-doesnt-exist')

from contextlib import asynccontextmanager
import os
import aiohttp
import time
from mergedeep import merge

# The base url for the Roblox API
RBX_API_URL = 'https://apis.roblox.com/'

# The base url for the Data Store API
DATASTORE_URL = RBX_API_URL + 'datastores/v1/universes/'

# The base url for the Ordered Data Store API
ORDERED_DATASTORE_URL = (
    RBX_API_URL + 'ordered-data-stores/v1/universes/{}/orderedDataStores/{}/scopes/{}/entries'
)

# The maximum number of retries 
MAX_RETRIES = 5

# Defining particular useful status response codes here
NO_CONTENT = 204
FORBIDDEN = 403
NOT_FOUND = 404
TOO_MANY_REQUESTS = 429 
BAD_GATEWAY = 502

class AsyncClientBase:
    """
    A base class for async Roblox API request clients.
    """
    def __init__(self, session):
        # The total number of retries (from rate limiting fails) for the session
        self.retries = 0
        # An instance of `aiohttp.ClientSession`
        self.session = session

    async def _request(self, *args, attempt=1, **kwargs):
        """
        Attempts to execute a request and parse the response.
        If a `Too Many Requests` (429) error response is returned
        the function waits for `2 ** attempt`
        then recurses incrementing `attempt` up to `MAX_RETRIES` times.
        """
        response = await self.session.request(*args, **kwargs)
        if response.status in (TOO_MANY_REQUESTS, BAD_GATEWAY):
            if attempt <= MAX_RETRIES:
                time.sleep(2 ** attempt)
                self.retries += 1
                return await self._request(*args, attempt=(attempt + 1), **kwargs)
        response.raise_for_status()
        if response.status != NO_CONTENT:
            return await response.json()


class AsyncDataStoreClient(AsyncClientBase):
    """
    Wraps a `aiohttp.ClientSession` with specific methods for using the Data Store API.
    """
    def __init__(self, session, universe_id, **base_params):
        super().__init__(session)
        # The base Data Store API url for a given place
        self.url = f'{DATASTORE_URL}{universe_id}/standard-datastores'
        # Parameters applied to all requests
        self.base_params = base_params

    async def list_datastores(self, **kwargs):
        """
        Lists a page of the names of the datastore belonging to an experience.
        Subsequent pages are requested with the `cursor` param.
        """
        return await self._request(
            'GET', self.url, params={**self.base_params, **kwargs}
        )

    async def list_entries(self, **kwargs):
        """
        Lists a page of entry keys for a given datastore.
        Subsequent pages are requested with the `cursor` param.
        """
        return await self._request(
            'GET', self.url + '/datastore/entries', params={**self.base_params, **kwargs}
        )

    async def get_entry(self, entry_key, **kwargs):
        """
        Retrieves an entry for a given key for a given datastore.
        """
        return await self._request('GET', self.url + '/datastore/entries/entry', params={
            'entryKey': entry_key, **self.base_params, **kwargs
        })

    async def set_entry(self, entry_key, data, **kwargs):
        """
        Set an entry for a given key for a given datastore.
        """
        url = self.url + '/datastore/entries/entry'

        return await self._request('POST', url, json=data, params={
            'entryKey': entry_key, **self.base_params, **kwargs
        })

    async def delete_entry(self, entry_key, **kwargs):
        """
        Marks an entry for a given key for a given datastore as deleted.
        The `datastoreName` request param must be given either with `base_params` or with `kwargs`.
        """
        return await self._request('DELETE', self.url + '/datastore/entries/entry', params={
            'entryKey': entry_key, **self.base_params, **kwargs
        })


class AsyncOrderedDataStoreClient(AsyncClientBase):
    """
    Wraps a `aiohttp.ClientSession` with specific methods for using the Ordered Data Store API.
    """
    def __init__(self, session, universe_id, ods_name, scope):
        super().__init__(session)
        # The base Data Store API url for the given args
        self.url = ORDERED_DATASTORE_URL.format(universe_id, ods_name, scope)

    async def list(self, **kwargs):
        """
        Lists a page of entries for a given datastore. Subsequent pages are requested
        with the `page_token` param.
        """
        return await self._request('GET', self.url, params=kwargs)

    async def delete(self, entry_id, **kwargs):
        """
        Deletes an entry for a given key.
        """
        return await self._request('DELETE', f'{self.url}/{entry_id}')


def with_x_api_key(kwargs):
    """
    Set the ROBLOX_API_KEY env var in `kwargs` as a `x-api-key` request header
    unless is it already there.
    """
    return merge(dict(headers={'x-api-key': os.environ.get('ROBLOX_API_KEY')}), kwargs)


@asynccontextmanager
async def ds_client(universe_id, base_params={}, **kwargs):
    """
    An `async` context manager that yields an `AsyncDataStoreClient`
    for a given place and data store.
    """
    async with aiohttp.ClientSession(**with_x_api_key(kwargs)) as session:
        yield AsyncDataStoreClient(session, universe_id, **base_params)


@asynccontextmanager
async def ods_client(universe_id, ods_name, scope='global', **kwargs):
    """
    An `async` context manager that yields an `AsyncOrderedDataStoreClient`
    for a given place and data store.
    """
    async with aiohttp.ClientSession(**with_x_api_key(kwargs)) as session:
        yield AsyncOrderedDataStoreClient(session, universe_id, ods_name, scope)


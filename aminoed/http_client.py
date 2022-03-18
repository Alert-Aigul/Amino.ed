from typing import Optional
from aiohttp import ClientSession
from aiohttp.client import ClientTimeout
from ujson import dumps

from .utils.helpers import generate_signature
from .utils.exceptions import CheckException


class AminoHttpClient:
    _session: ClientSession = None
    api: str = "https://service.narvii.com/api/v1"

    headers = {
        "Accept-Language": "en-En",
        "Content-Type"   : "application/json; charset=utf-8"
    }

    @property
    def session(self) -> ClientSession:
        if not self._session or self._session.closed:
            self._session = ClientSession(timeout=ClientTimeout(60), json_serialize=dumps)
        return self._session
    
    @session.setter
    def session(self, session: ClientSession) -> None:
        self._session = session
    
    @property
    def userId(self) -> ClientSession:
        userId: Optional[str] = self.headers.get("AUID")
        return userId if userId else None
    
    @userId.setter
    def userId(self, userId: str) -> None:
        self.headers["AUID"] = userId
    
    @property
    def deviceId(self) -> Optional[str]:
        deviceId: Optional[str] = self.headers.get("NDCDEVICEID")
        return deviceId if deviceId else None

    @deviceId.setter
    def deviceId(self, device_id: str) -> None:
        self.headers["NDCDEVICEID"] = device_id

    @property
    def sid(self) -> Optional[str]:
        sid: Optional[str] = self.headers.get("NDCAUTH")
        return sid.split("=")[1] if sid else None

    @sid.setter
    def sid(self, sid: str) -> None:
        self.headers["NDCAUTH"] = f"sid={sid}"
    
    @property
    def content_type(self) -> Optional[str]:
        type: Optional[str] = self.headers.get("Content-Type")
        return type if type else None
    
    async def post(self, url: str, json: dict = None, data: str = None, type: str = None):
        headers = self.headers
        headers["Content-Type"] = type or self.content_type
        headers["NDC-MSG-SIG"] = await generate_signature(dumps(json) if json else data)

        async with self._session.post(f"{self.api}{url}", 
                json=json, data=data, headers=headers) as response:

            if (json := await response.json())["api:statuscode"] != 0:
                return CheckException(json)
            return response

    async def get(self, url: str):
        async with self._session.get(f"{self.api}{url}",
                headers=self.headers) as response:

            if (json := await response.json())["api:statuscode"] != 0:
                return CheckException(json)
            return response
    
    async def delete(self, url: str):
        async with self._session.delete(f"{self.api}{url}",
                headers=self.headers) as response:

            if (json := await response.json())["api:statuscode"] != 0:
                return CheckException(json)
            return response
    
    async def post_request(self, url: str, json: dict = None, data: str = None, headers: dict = None):
        return await self._session.post(url, json=json, data=data, headers=headers)

    async def get_request(self, url: str, headers: dict = None):
        return await self._session.get(url, headers=headers)

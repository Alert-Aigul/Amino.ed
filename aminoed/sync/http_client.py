from time import time
from typing import ClassVar, Optional
from requests import Session, Response
from ujson import dumps

from .utils.helpers import generate_signature, is_json
from .utils.exceptions import CheckException


class AminoHttpClient:
    proxies: Optional[dict] = None
    _session: Optional[Session] = None
    api: ClassVar = "https://service.narvii.com/api/v1"

    headers = {
        "Accept-Language": "en-En",
        "Content-Type"   : "application/json; charset=utf-8",
        "NDCDEVICEID"    : "4240460afcb124fe8e9ac55133749c7027a160df0e853211adc49848822952b6efa10f9c657c3c9665",
        "User-Agent"     : "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Mobile Safari/537.36"
    }

    @property
    def session(self) -> Session:
        if not self._session:
            self._session = Session()
        return self._session
    
    @session.setter
    def session(self, session: Session) -> None:
        self._session = session
    
    @property
    def userId(self) -> Session:
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
    
    def post(self, url: str, json: dict = None, data: str = None, type: str = None) -> Response:
        headers = self.headers.copy()
        headers["Content-Type"] = type or self.content_type

        if json is not None:
            json["timestamp"] = int(time() * 1000)        
            data = dumps(json)

        if data is not None:
            headers["NDC-MSG-SIG"] = generate_signature(data)

        response = self._session.post(f"{self.api}{url}", data=data, headers=headers, proxies=self.proxies)
        
        if not is_json((json := response.text)) or response.status_code != 200:
            return CheckException(json)
        return response

    def get(self, url: str) -> Response:
        response = self._session.get(f"{self.api}{url}", headers=self.headers, proxies=self.proxies)

        if not is_json((json := response.text)) or response.status_code != 200:
            return CheckException(json)
        return response
    
    def delete(self, url: str) -> Response:
        response = self._session.delete(f"{self.api}{url}", headers=self.headers, proxies=self.proxies)

        if not is_json((json := response.text)) or response.status_code != 200:
            return CheckException(json)
        return response
    
    def post_request(self, url: str, json: dict = None, data: str = None, headers: dict = None) -> Response:
        return self._session.post(url, json=json, data=data,
            headers=headers, proxies=self.proxies)

    def get_request(self, url: str, headers: dict = None) -> Response:
        return self._session.get(url, headers=headers, proxies=self.proxies)

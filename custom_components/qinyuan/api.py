"""API client for Qinyuan and Aliyun Link Living platforms."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

QINYUAN_API_BASE = "https://iot2.qinyuan.cn"
ALIYUN_API_BASE = "https://api.link.aliyun.com"
DEFAULT_APP_KEY = "24904714"


class QinyuanApiClient:
    """Client for interacting with Qinyuan Cloud and Aliyun Living IoT APIs."""

    def __init__(
        self,
        auth_token: str,
        iot_token: str | None = None,
        app_secret: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.auth_token = auth_token
        self.iot_token = iot_token
        self.app_secret = app_secret
        self._session = session
        self._owns_session = False

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the underlying aiohttp session if owned."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def async_get_device_list(self) -> list[dict[str, Any]]:
        """Fetch the list of devices bound to the user account."""
        session = await self._get_session()
        url = f"{QINYUAN_API_BASE}/web/api/app/device/list"
        headers = {
            "Authorization": self.auth_token,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "Accept": "application/json",
        }
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        return data.get("data", [])
                _LOGGER.error("Failed to get device list: HTTP %s", resp.status)
        except Exception as err:
            _LOGGER.error("Exception while getting device list: %s", err)
        return []

    async def async_get_filter_detail(self, iot_id: str, product_key: str) -> list[dict[str, Any]]:
        """Fetch filter life details for a device."""
        session = await self._get_session()
        url = f"{QINYUAN_API_BASE}/web/api/app/device/filter/detail?iotId={iot_id}&productKey={product_key}"
        headers = {
            "Authorization": self.auth_token,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "Accept": "application/json",
        }
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success") or data.get("code") == 100:
                        return data.get("data", {}).get("filterDetail", [])
        except Exception as err:
            _LOGGER.error("Exception while getting filter detail: %s", err)
        return []

    async def async_get_device_detail(self, device_id: str) -> dict[str, Any]:
        """Fetch detail info for a device."""
        session = await self._get_session()
        url = f"{QINYUAN_API_BASE}/web/api/app/device/deviceDetail?deviceId={device_id}&type=2&version=3.3"
        headers = {
            "Authorization": self.auth_token,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "Accept": "application/json",
        }
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        return data.get("data", {})
        except Exception as err:
            _LOGGER.error("Exception while getting device detail: %s", err)
        return {}

    async def async_get_aliyun_properties(self, iot_id: str) -> dict[str, Any]:
        """Query real-time properties from Aliyun Living IoT if AppSecret is configured."""
        if not self.app_secret or not self.iot_token:
            return {}

        session = await self._get_session()
        url = f"{ALIYUN_API_BASE}/thing/properties/get"
        path = "/thing/properties/get"
        req_id = str(uuid.uuid4()).upper()
        nonce = str(uuid.uuid4()).upper()
        timestamp = str(int(time.time() * 1000))

        body_dict = {
            "id": req_id,
            "params": {"iotId": iot_id},
            "request": {
                "language": "zh-CN",
                "appKey": DEFAULT_APP_KEY,
                "iotToken": self.iot_token,
                "apiVer": "1.0.2",
            },
            "version": "1.0.0",
        }
        body_bytes = json.dumps(body_dict).encode("utf-8")

        # Construct StringToSign according to Aliyun API Gateway specification
        # Method\nAccept\n\nContent-Type\n\nX-Ca-Key:...\nX-Ca-Nonce:...\nX-Ca-Stage:...\nX-Ca-Timestamp:...\nX-Ca-Version:...\nPath
        accept = "application/json; charset=UTF-8"
        content_type = "application/json; charset=UTF-8"
        headers_to_sign = [
            f"X-Ca-Key:{DEFAULT_APP_KEY}",
            f"X-Ca-Nonce:{nonce}",
            f"X-Ca-Stage:RELEASE",
            f"X-Ca-Timestamp:{timestamp}",
            f"X-Ca-Version:1",
        ]
        string_to_sign = f"POST\n{accept}\n\n{content_type}\n\n" + "\n".join(headers_to_sign) + f"\n{path}"

        sig = base64.b64encode(
            hmac.new(self.app_secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1).digest()
        ).decode("utf-8")

        headers = {
            "Content-Type": content_type,
            "Accept": accept,
            "User-Agent": "iOS-IMSApiClient-1.7.3",
            "X-Ca-Key": DEFAULT_APP_KEY,
            "X-Ca-Version": "1",
            "X-Ca-Stage": "RELEASE",
            "X-Ca-Timestamp": timestamp,
            "X-Ca-Nonce": nonce,
            "X-Ca-Signature-Headers": "X-Ca-Version,X-Ca-Nonce,X-Ca-Timestamp,X-Ca-Stage,X-Ca-Key",
            "X-Ca-Signature-Method": "HmacSHA1",
            "X-Ca-Signature": sig,
        }

        try:
            async with session.post(url, data=body_bytes, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    if res_json.get("code") == 200:
                        return res_json.get("data", {})
                _LOGGER.warning("Aliyun properties query returned HTTP %s", resp.status)
        except Exception as err:
            _LOGGER.error("Exception querying Aliyun properties: %s", err)
        return {}

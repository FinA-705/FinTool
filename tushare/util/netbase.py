# -*- coding:utf-8 -*- 

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

import asyncio
import aiohttp


class Client(object):
    def __init__(self, url=None, ref=None, cookie=None):
        self._ref = ref
        self._cookie = cookie
        self._url = url
        self._setOpener()
        
    def _setOpener(self):
        request = Request(self._url)
        request.add_header("Accept-Language", "en-US,en;q=0.5")
        request.add_header("Connection", "keep-alive")
#         request.add_header('Referer', self._ref)
        if self._cookie is not None:
            request.add_header("Cookie", self._cookie)
        request.add_header("User-Agent", 'Mozilla/5.0 (Windows NT 6.1; rv:37.0) Gecko/20100101 Firefox/37.0')
        self._request = request
        
    def gvalue(self):
        values = urlopen(self._request, timeout = 10).read()
        return values


class AsyncClient(object):
    """异步版本的HTTP客户端"""
    def __init__(self, url=None, ref=None, cookie=None, timeout=10):
        self._ref = ref
        self._cookie = cookie
        self._url = url
        self._timeout = timeout
        self._headers = self._build_headers()
        
    def _build_headers(self):
        headers = {
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "User-Agent": 'Mozilla/5.0 (Windows NT 6.1; rv:37.0) Gecko/20100101 Firefox/37.0'
        }
        if self._cookie is not None:
            headers["Cookie"] = self._cookie
        return headers
        
    async def gvalue(self):
        """异步获取数据"""
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        async with aiohttp.ClientSession(timeout=timeout, headers=self._headers) as session:
            async with session.get(self._url) as response:
                return await response.read()

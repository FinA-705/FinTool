# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pro数据接口
Created on 2017/07/01
@author: polo,Jimmy
@group : https://waditu.com
"""

from typing import Any, Callable, Coroutine
import pandas as pd
import json
from functools import partial
import requests
import asyncio
import aiohttp


class DataApi:

    __token = ""
    __http_url = "http://api.waditu.com/dataapi"
    # __http_url = 'http://127.0.0.1:8000/dataapi'

    def __init__(self, token, timeout=30):
        """
        Parameters
        ----------
        token: str
            API接口TOKEN，用于用户认证
        """
        self.__token = token
        self.__timeout = timeout

    def query(self, api_name, fields="", **kwargs):
        req_params = {
            "api_name": api_name,
            "token": self.__token,
            "params": kwargs,
            "fields": fields,
        }

        res = requests.post(
            f"{self.__http_url}/{api_name}", json=req_params, timeout=self.__timeout
        )
        if res:
            result = json.loads(res.text)
            if result["code"] != 0:
                raise Exception(result["msg"])
            data = result["data"]
            columns = data["fields"]
            items = data["items"]
            return pd.DataFrame(items, columns=columns)
        else:
            return pd.DataFrame()

    def __getattr__(self, name):
        return partial(self.query, name)


class AsyncDataApi:
    """异步版本的Pro数据接口"""

    __token = ""
    __http_url = "http://api.waditu.com/dataapi"

    def __init__(self, token, timeout=30):
        """
        Parameters
        ----------
        token: str
            API接口TOKEN，用于用户认证
        timeout: int
            请求超时时间（秒）
        """
        self.__token = token
        self.__timeout = timeout

    async def query(self, api_name, fields="", **kwargs):
        """异步查询数据"""
        req_params = {
            "api_name": api_name,
            "token": self.__token,
            "params": kwargs,
            "fields": fields,
        }

        timeout = aiohttp.ClientTimeout(total=self.__timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.__http_url}/{api_name}", json=req_params
            ) as res:
                if res.status == 200:
                    result_text = await res.text()
                    result = json.loads(result_text)
                    if result["code"] != 0:
                        raise Exception(result["msg"])
                    data = result["data"]
                    columns = data["fields"]
                    items = data["items"]
                    return pd.DataFrame(items, columns=columns)
                else:
                    return pd.DataFrame()

    def __getattr__(self, name) -> Callable[..., Coroutine[Any, Any, Any]]:
        async def async_query(*args, **kwargs):
            return await self.query(name, *args, **kwargs)

        return async_query

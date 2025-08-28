import json
import asyncio

import requests
import aiohttp
try:
    import sseclient
except:
    raise ImportError("sseclient not found, please install it using 'pip install sseclient-py'.")


from tushare import get_token

BASE_URL = "http://api.waditu.com/dataapi"
# BASE_URL = "http://10.255.255.205:8083/dataapi"
API_KEY_PREFIX = "tsgpt-"


class GPTClient:
    def __init__(self, token=None, timetout=120):
        if not token:
            token = get_token()
        self.token = token
        self.timeout = timetout

    def _request(self, model, messages, temperature=None, max_tokens=None, stream=True, pretty=False) -> requests.Response:
        """
        model string 模型名称， doubao-pro-128k
        messages list 消息列表
            [
                {
                  "role": "user",
                  "content": "Hello World"
                }
            ]
        pretty bool 是否只返回回答内容文本
        """
        resp = requests.post(
            f'{BASE_URL}/llm/{model}',
            json={"params": {
                "stream": stream,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }},
            headers={"Authorization": f"tstoken-{self.token}"},
            timeout=self.timeout, stream=stream
        )
        if resp.status_code != 200:
            raise Exception(f"请求出现错误，{resp.content}")
        return resp

    def gpt_query(self, model, messages, temperature=None, max_tokens=None, pretty=False):
        resp = self._request(model, messages, temperature, max_tokens, False, pretty)
        resp_data = resp.json()
        if resp_data.get('code') not in (0, None):
            raise Exception(resp_data.get('msg') or resp_data)
        if pretty:
            return resp_data['choices'][0]["message"]["content"]
        else:
            return resp_data

    def gpt_stream(self, model, messages, temperature=None, max_tokens=None, pretty=False):
        resp = self._request(model, messages, temperature, max_tokens, True, pretty)
        for e in sseclient.SSEClient(resp).events():
            if '[DONE]' in e.data.upper():
                break
            e_data = json.loads(e.data)
            if pretty:
                yield e_data["choices"][0]["delta"]["content"]
            else:
                yield e_data

    def gpt(self, model, query) -> str:
        messages = [{
          "role": "user",
          "content": query
        }]
        return self.gpt_query(model, messages, pretty=True)


class AsyncGPTClient:
    """异步版本的GPT客户端"""
    def __init__(self, token=None, timeout=120):
        if not token:
            token = get_token()
        self.token = token
        self.timeout = timeout

    async def _request(self, model, messages, temperature=None, max_tokens=None, stream=True, pretty=False):
        """异步请求方法"""
        url = f'{BASE_URL}/llm/{model}'
        headers = {"Authorization": f"tstoken-{self.token}"}
        json_data = {"params": {
            "stream": stream,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }}
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=json_data, headers=headers) as resp:
                if resp.status != 200:
                    content = await resp.read()
                    raise Exception(f"请求出现错误，{content}")
                return resp

    async def gpt_query(self, model, messages, temperature=None, max_tokens=None, pretty=False):
        """异步查询GPT"""
        url = f'{BASE_URL}/llm/{model}'
        headers = {"Authorization": f"tstoken-{self.token}"}
        json_data = {"params": {
            "stream": False,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }}
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=json_data, headers=headers) as resp:
                if resp.status != 200:
                    content = await resp.read()
                    raise Exception(f"请求出现错误，{content}")
                
                resp_text = await resp.text()
                resp_data = json.loads(resp_text)
                if resp_data.get('code') not in (0, None):
                    raise Exception(resp_data.get('msg') or resp_data)
                if pretty:
                    return resp_data['choices'][0]["message"]["content"]
                else:
                    return resp_data

    async def gpt_stream(self, model, messages, temperature=None, max_tokens=None, pretty=False):
        """异步流式查询GPT"""
        url = f'{BASE_URL}/llm/{model}'
        headers = {"Authorization": f"tstoken-{self.token}"}
        json_data = {"params": {
            "stream": True,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }}
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=json_data, headers=headers) as resp:
                if resp.status != 200:
                    content = await resp.read()
                    raise Exception(f"请求出现错误，{content}")
                
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]  # 移除 'data: ' 前缀
                        if '[DONE]' in data.upper():
                            break
                        try:
                            e_data = json.loads(data)
                            if pretty:
                                content = e_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            else:
                                yield e_data
                        except json.JSONDecodeError:
                            continue

    async def gpt(self, model, query) -> str:
        """异步简化接口"""
        messages = [{
            "role": "user",
            "content": query
        }]
        return await self.gpt_query(model, messages, pretty=True)


def test_gpt_query():
    c = GPTClient()
    dd = c.gpt_query("doubao-pro-128k", [{
        "role": "user",
        "content": "你好"
    }])
    print(dd)
    dd = c.gpt_query("doubao-pro-128k", [{
        "role": "user",
        "content": "你好"
    }], pretty=True)
    print(dd)


def test_gpt_stream():
    c = GPTClient()
    dd = c.gpt_stream("doubao-pro-128k", [
        {
            "role": "user",
            "content": "你好"
        }
    ])
    for d in dd:
        print(d)

    dd = c.gpt_stream("doubao-pro-128k", [
        {
            "role": "user",
            "content": "你好"
        }
    ], pretty=True)
    for d in dd:
        print(d)


def test_gpt():
    c = GPTClient()
    dd = c.gpt("doubao-pro-128k", "你好")
    print(dd)

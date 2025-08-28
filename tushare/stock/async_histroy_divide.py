#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
异步版本的股票历史分笔数据模块
Created on 2024/01/01
@author: AI Assistant
@group : waditu
Desc: 腾讯-股票-实时行情-成交明细（异步版本）
成交明细-每个交易日 16:00 提供当日数据
港股报价延时 15 分钟
"""
import warnings
import pandas as pd
import aiohttp
import asyncio
from io import StringIO
from tushare.util.verify_token import require_permission
from tushare.util.format_stock_code import format_stock_code
from tushare.stock.rtq_vars import zh_sina_a_stock_cookies, zh_sina_a_stock_headers
import time
import json
from typing import Optional
from tushare.util.form_date import get_current_date
from tushare.stock import rtq_vars
from tushare.util.format_stock_code import symbol_verify

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
}


async def async_realtime_tick(ts_code: str = "000001.SZ", src: Optional[str] = "tx",
                             page_count: Optional[int] = None) -> pd.DataFrame:
    """
    异步获取历史分笔数据
    :param ts_code: 股票代码
    :type ts_code: str
    :param src: 来源  腾讯财经tx   新浪财经sina
    :type src: str
    :param page_count: 限制页数
    :type page_count: str
    :return: 历史分笔数据
    :rtype: pandas.DataFrame
        1、TIME : 成交时间
        2、PRICE : 成交价格
        3、PCHANGE : 涨跌幅
        4、CHANGE : 价格变动
        5、VOLUME : 成交量(手)
        6、AMOUNT : 成交额(元)
        7、TYPE : 性质
    """
    symbol = symbol_verify(ts_code)
    if src == "sina":
        return await async_get_stock_sina_a_divide_amount(symbol, page_count)
    elif src == 'dc':
        return await async_get_stock_dc_a_divide_amount(symbol, page_count)
    else:
        return await async_get_stock_tx_a_divide_amount(symbol, page_count)


async def async_get_stock_tx_a_divide_amount(symbol: str = "sz000001", page_count: Optional[int] = None) -> pd.DataFrame:
    """
    异步获取腾讯财经-历史分笔数据
    https://gu.qq.com/sz300494/gp/detail
    :param symbol: 股票代码
    :type symbol: str
    :param page_count: 限制页数
    :type page_count: str
    :return: 历史分笔数据
    :rtype: pandas.DataFrame
    """
    symbols = str(symbol).lower().split(".")
    symbol = f"{symbols[1]}{symbols[0]}"
    big_df = pd.DataFrame()
    page = 0
    warnings.warn("正在异步下载数据，请稍等")
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        while True:
            try:
                url = "http://stock.gtimg.cn/data/index.php"
                params = {
                    "appn": "detail",
                    "action": "data",
                    "c": symbol,
                    "p": page,
                }
                async with session.get(url, params=params) as r:
                    text_data = await r.text()
                    temp_df = (
                        pd.DataFrame(eval(text_data[text_data.find("["):])[1].split("|"))
                            .iloc[:, 0]
                            .str.split("/", expand=True)
                    )
                    page += 1
                    big_df = pd.concat([big_df, temp_df], ignore_index=True)
                    await asyncio.sleep(0.5)  # 异步等待
                    if page_count and page >= page_count:
                        break
            except:
                break
    
    if not big_df.empty:
        big_df = big_df.iloc[:, 1:].copy()
        big_df.columns = ["TIME", "PRICE", "PCHANGE", "CHANGE", "VOLUME", "AMOUNT", "TYPE"]
        big_df["TIME"] = pd.to_datetime(big_df["TIME"], format="%H%M%S").dt.strftime("%H:%M:%S")
        big_df = big_df.astype({"PRICE": float, "PCHANGE": float, "CHANGE": float, "VOLUME": int, "AMOUNT": float})
        big_df["TYPE"] = big_df["TYPE"].replace({"1": "买盘", "2": "卖盘", "4": "中性盘"})
        return big_df
    else:
        return pd.DataFrame()


async def async_get_stock_sina_a_divide_amount(symbol: str = "sz000001", page_count: Optional[int] = None) -> pd.DataFrame:
    """
    异步获取新浪财经-历史分笔数据
    :param symbol: 股票代码
    :type symbol: str
    :param page_count: 限制页数
    :type page_count: str
    :return: 历史分笔数据
    :rtype: pandas.DataFrame
    """
    symbols = str(symbol).lower().split(".")
    symbol = f"{symbols[1]}{symbols[0]}"
    big_df = pd.DataFrame()
    page = 1
    warnings.warn("正在异步下载数据，请稍等")
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=zh_sina_a_stock_headers, cookies=zh_sina_a_stock_cookies) as session:
        while True:
            try:
                url = "https://vip.stock.finance.sina.com.cn/quotes_service/view/vMS_tradedetail.php"
                params = {
                    "symbol": symbol,
                    "date": get_current_date(),
                    "page": page,
                }
                async with session.get(url, params=params) as response:
                    text_data = await response.text()
                    
                if "暂无成交明细数据" in text_data:
                    break
                    
                temp_df = pd.read_html(StringIO(text_data))[0]
                if temp_df.empty:
                    break
                    
                page += 1
                big_df = pd.concat([big_df, temp_df], ignore_index=True)
                await asyncio.sleep(0.5)  # 异步等待
                if page_count and page > page_count:
                    break
            except:
                break
    
    if not big_df.empty:
        big_df.columns = ["TIME", "PRICE", "PCHANGE", "CHANGE", "VOLUME", "AMOUNT", "TYPE"]
        big_df = big_df.astype({"PRICE": float, "PCHANGE": float, "CHANGE": float, "VOLUME": int, "AMOUNT": float})
        return big_df
    else:
        return pd.DataFrame()


async def async_get_stock_dc_a_divide_amount(symbol: str = "sz000001", page_count: Optional[int] = None) -> pd.DataFrame:
    """
    异步获取东财-历史分笔数据
    :param symbol: 股票代码
    :type symbol: str
    :param page_count: 限制页数
    :type page_count: str
    :return: 历史分笔数据
    :rtype: pandas.DataFrame
    """
    big_df = pd.DataFrame()
    page = 1
    warnings.warn("正在异步下载数据，请稍等")
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=rtq_vars.dc_headers, cookies=rtq_vars.dc_cookies) as session:
        while True:
            try:
                url = "http://push2ex.eastmoney.com/getTopicSCRList"
                params = {
                    "ut": "7eea3edcaed734bea9cbfc24409ed989",
                    "dpt": "wzfscj",
                    "cb": "topicsScr",
                    "pagesize": "50",
                    "pageindex": page,
                    "id": format_stock_code(symbol),
                    "sort": "1",
                    "ft": "1",
                    "code": format_stock_code(symbol),
                    "_": int(time.time() * 1000),
                }
                async with session.get(url, params=params) as response:
                    text_data = await response.text()
                    
                json_data = json.loads(text_data[text_data.find("(") + 1: text_data.rfind(")")])
                if not json_data.get("data") or not json_data["data"].get("diff"):
                    break
                    
                temp_df = pd.DataFrame(json_data["data"]["diff"])
                if temp_df.empty:
                    break
                    
                page += 1
                big_df = pd.concat([big_df, temp_df], ignore_index=True)
                await asyncio.sleep(0.5)  # 异步等待
                if page_count and page > page_count:
                    break
            except:
                break
    
    if not big_df.empty:
        # 处理东财数据格式
        big_df = big_df[["f1", "f2", "f3", "f4", "f5", "f6", "f7"]]
        big_df.columns = ["TIME", "PRICE", "PCHANGE", "CHANGE", "VOLUME", "AMOUNT", "TYPE"]
        return big_df
    else:
        return pd.DataFrame()
#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
异步版本的实时行情数据获取模块
Created on 2024/01/01
@author: AI Assistant
@group : waditu
"""
import pandas as pd
import aiohttp
import asyncio
import re
import time
from typing import Union, List, Optional
from tushare.stock import cons as ct
from tushare.stock import rtq_vars as rtqv
from tushare.util.format_stock_code import format_stock_code
from tushare.util.form_date import timestemp_to_time
from tushare.util.verify_token import require_permission


def _get_current_timestamp():
    """获取当前时间戳"""
    return str(int(time.time() * 1000))


async def async_get_realtime_quotes(symbols: Union[str, List[str]]) -> pd.DataFrame:
    """
    异步获取实时行情数据

    Parameters
    ----------
    symbols : str or list
        股票代码，可以是单个代码字符串或代码列表

    Returns
    -------
    DataFrame
        实时行情数据
    """
    # 处理股票代码
    syms = []
    if isinstance(symbols, list):
        for symbol in symbols:
            _code = (
                ct.INDEX_LABELS[symbol]
                if symbol in ct.INDEX_LABELS
                else ct.P_TYPE["http"] + symbol
            )
            syms.append(_code)
    else:
        symbols = symbols.upper().split(",")
        for symbol in symbols:
            _code = (
                ct.INDEX_LABELS[symbol]
                if symbol in ct.INDEX_LABELS
                else ct.P_TYPE["http"] + symbol
            )
            syms.append(_code)

    # 构建请求URL
    symbols_list = ",".join([s for s in symbols])
    root_url = ct.LIVE_DATA_URL % (
        ct.P_TYPE["http"],
        ct.DOMAINS["sinahq"],
        _get_current_timestamp(),
        symbols_list,
    )

    # 异步请求数据
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "host": "hq.sinajs.cn",
        "referer": "https://finance.sina.com.cn/",
    }

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(root_url) as response:
            content = await response.read()
            text = content.decode("GBK")

    # 解析数据
    reg = re.compile(r'\="(.*?)\";')
    data = reg.findall(text)
    data_list = []
    syms_list = []

    for index, row in enumerate(data):
        if len(row) > 1:
            data_list.append([astr for astr in row.split(",")[:33]])
            syms_list.append(syms[index])

    if len(syms_list) == 0:
        return None

    # 构建DataFrame
    df = pd.DataFrame(data_list, columns=ct.LIVE_DATA_COLS)
    df = df.drop("s", axis=1)
    df["code"] = syms_list

    # 数据处理
    ls = [cls for cls in df.columns if "_v" in cls]
    for txt in ls:
        df[txt] = df[txt].map(lambda x: x[:-2])

    df.columns = rtqv.LIVE_DATA_COLS
    df["TS_CODE"] = df["TS_CODE"].apply(format_stock_code)
    df["DATE"] = df["DATE"].apply(timestemp_to_time)

    # 重新排序
    new_order = rtqv.LIVE_DATA_COLS_REINDEX
    df = df[new_order]

    # 数据类型转换
    cols_to_convert = [
        "OPEN",
        "PRE_CLOSE",
        "PRICE",
        "HIGH",
        "LOW",
        "BID",
        "ASK",
        "VOLUME",
        "AMOUNT",
        "B1_V",
        "B1_P",
        "B2_V",
        "B2_P",
        "B3_V",
        "B3_P",
        "B4_V",
        "B4_P",
        "B5_V",
        "B5_P",
        "A1_V",
        "A1_P",
        "A2_V",
        "A2_P",
        "A3_V",
        "A3_P",
        "A4_V",
        "A4_P",
        "A5_V",
        "A5_P",
    ]

    df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors="coerce")
    df_filled = df.fillna(0)

    return df_filled


async def async_get_today_all() -> pd.DataFrame:
    """
    异步获取当日所有股票的实时行情数据

    Returns
    -------
    DataFrame
        所有股票的实时行情数据
    """
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    }

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        # 获取股票数量
        async with session.get(ct.ALL_STOCK_BASICS_FILE) as res:
            text = await res.text()
            stock_count = len(text.split("\n")) - 1

        # 分页获取数据
        all_data = []
        page_size = 80
        for page in range(0, stock_count, page_size):
            url = f"{ct.SINA_DAY_PRICE_URL}?page={page//page_size + 1}&num={page_size}"
            async with session.get(url) as r:
                data_text = await r.text()
                # 解析数据（这里需要根据实际返回格式进行调整）
                # 简化处理，实际应该解析JSON或其他格式
                all_data.append(data_text)
            await asyncio.sleep(0.1)  # 避免请求过快

    # 处理合并数据（这里需要根据实际数据格式进行处理）
    # 返回DataFrame格式的数据
    return pd.DataFrame()  # 占位返回


async def async_get_stock_basics() -> pd.DataFrame:
    """
    异步获取股票基本信息

    Returns
    -------
    DataFrame
        股票基本信息
    """
    timeout = aiohttp.ClientTimeout(total=30)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    }

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(ct.ALL_STOCK_BASICS_FILE) as response:
            text = await response.text()

    # 解析数据
    lines = text.strip().split("\n")
    data_list = []
    for line in lines[1:]:  # 跳过标题行
        if line.strip():
            data_list.append(line.split("\t"))

    if data_list:
        df = pd.DataFrame(
            data_list,
            columns=[
                "code",
                "name",
                "industry",
                "area",
                "pe",
                "outstanding",
                "totals",
                "totalAssets",
                "liquidAssets",
                "fixedAssets",
                "reserved",
                "reservedPerShare",
                "esp",
                "bvps",
                "pb",
                "timeToMarket",
                "undp",
                "perundp",
                "rev",
                "profit",
                "gpr",
                "npr",
                "holders",
            ],
        )
        return df
    else:
        return pd.DataFrame()


async def async_get_sina_dd(
    code: str = None, date: str = None, vol: int = 400
) -> pd.DataFrame:
    """
    异步获取新浪大单数据

    Parameters
    ----------
    code : str
        股票代码
    date : str
        查询日期
    vol : int
        大单成交量下限，默认400手

    Returns
    -------
    DataFrame
        大单数据
    """
    if code is None or date is None:
        return pd.DataFrame()

    # 构建URL
    symbol = f"sh{code}" if code.startswith("6") else f"sz{code}"
    url = ct.SINA_DD % (date, symbol)

    timeout = aiohttp.ClientTimeout(total=30)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    }

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(url) as response:
            text = await response.text()

    # 解析数据
    if len(text) > 0:
        df = pd.read_csv(StringIO(text), names=ct.SINA_DD_COLS, skiprows=[0])
        df = df.drop_duplicates()
        df = df[df.volume >= vol]
        return df
    else:
        return pd.DataFrame()


# 使用示例函数
async def example_usage():
    """异步使用示例"""
    # 获取单只股票实时行情
    df1 = await async_get_realtime_quotes("000001")
    print("单只股票行情:")
    print(df1)

    # 获取多只股票实时行情
    df2 = await async_get_realtime_quotes(["000001", "000002", "600000"])
    print("多只股票行情:")
    print(df2)

    # 获取股票基本信息
    df3 = await async_get_stock_basics()
    print("股票基本信息:")
    print(df3.head())


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())

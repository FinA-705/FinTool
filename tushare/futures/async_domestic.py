#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
异步版本的国内期货数据获取模块
Created on 2024/01/01
@author: AI Assistant
@contact: ai@assistant.com
'''

import json
import datetime
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from tushare.futures import domestic_cons as ct


async def async_get_cffex_daily(date=None):
    """
    异步获取中金所日交易数据
    Parameters
    ------
        date: 日期 format：YYYY-MM-DD 或 YYYYMMDD 或 datetime.date对象 为空时为当天
    Return
    -------
        DataFrame
            中金所日交易数据(DataFrame):
                symbol        合约代码
                date          日期
                open          开盘价
                high          最高价
                low          最低价
                close         收盘价
                volume        成交量
                open_interest   持仓量
                turnover      成交额
                settle        结算价
                pre_settle    前结算价
                variety       合约类别
        或 None(给定日期没有交易数据)
    """
    day = ct.convert_date(date) if date is not None else datetime.date.today()
    
    try:
        url = ct.CFFEX_DAILY_URL % (day.strftime('%Y%m'), day.strftime('%d'), day.strftime('%Y%m%d'))
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=ct.SIM_HAEDERS) as response:
                html = await response.text(encoding='gbk', errors='ignore')
        
        if html.find(u'网页错误') >= 0:
            return None
            
        html_soup = BeautifulSoup(html, 'html.parser')
        data_table = html_soup.find_all('tr')
        
        if len(data_table) <= 1:
            return None
        
        dict_data = []
        day_const = int(day.strftime('%Y%m%d'))
        
        for idata in data_table[1:]:
            x = idata.find_all('td')
            if len(x) == 0:
                continue
            row_data = [ix.text.strip() for ix in x]
            
            if len(row_data) < len(ct.CFFEX_COLUMNS):
                continue
                
            m = ct.FUTURE_SYMBOL_PATTERN.match(row_data[0])
            if not m:
                continue
            row_dict = {}
            
            for i, field in enumerate(ct.CFFEX_COLUMNS):
                if i < len(row_data):
                    if row_data[i] == u'':
                        row_dict[field] = 0.0
                    else:
                        try:
                            row_dict[field] = float(row_data[i].replace(',', ''))
                        except:
                            row_dict[field] = row_data[i]
            
            row_dict['date'] = day_const
            row_dict['symbol'] = row_data[0]
            row_dict['variety'] = m.group(1).upper()
            dict_data.append(row_dict)
        
        if len(dict_data) == 0:
            return None
        
        return pd.DataFrame(dict_data)[ct.OUTPUT_COLUMNS]
        
    except Exception as e:
        print(f"获取中金所数据失败: {e}")
        return None


async def async_get_czce_daily(date=None, type="future"):
    """
    异步获取郑商所日交易数据
    Parameters
    ------
        date: 日期 format：YYYY-MM-DD 或 YYYYMMDD 或 datetime.date对象 为空时为当天
        type: 数据类型, 为'future'期货 或 'option'期权二者之一
    Return
    -------
        DataFrame 或 None
    """
    if type == 'future':
        url = ct.CZCE_DAILY_URL
        listed_columns = ct.CZCE_COLUMNS
        output_columns = ct.OUTPUT_COLUMNS
    elif type == 'option':
        url = ct.CZCE_OPTION_URL
        listed_columns = ct.CZCE_OPTION_COLUMNS
        output_columns = ct.OPTION_OUTPUT_COLUMNS
    else:
        print('invalid type :' + type + ',type should be one of "future" or "option"')
        return None
    
    day = ct.convert_date(date) if date is not None else datetime.date.today()

    try:
        request_url = url % (day.strftime('%Y'), day.strftime('%Y%m%d'))
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(request_url, headers=ct.SIM_HAEDERS) as response:
                if response.status == 404:
                    return None
                html = await response.text(encoding='gbk', errors='ignore')
                
    except Exception as e:
        print(f"请求郑商所数据失败: {e}")
        return None
    
    if html.find(u'您的访问出错了') >= 0 or html.find(u'无期权每日行情交易记录') >= 0:
        return None
        
    html = [i.replace(' ','').split('|') for i in html.split('\n')[:-4] if i[0][0] != u'小']
    
    if len(html) < 2 or html[1][0] not in [u'品种月份', u'品种代码']:
        return None
        
    dict_data = list()
    day_const = int(day.strftime('%Y%m%d'))
    
    for row in html[2:]:
        m = ct.FUTURE_SYMBOL_PATTERN.match(row[0])
        if not m:
            continue
        row_dict = {}
        
        for i, field in enumerate(listed_columns):
            if i < len(row):
                if row[i] == u'':
                    row_dict[field] = 0.0
                else:
                    try:
                        row_dict[field] = float(row[i].replace(',', ''))
                    except:
                        row_dict[field] = row[i]
        
        row_dict['date'] = day_const
        row_dict['symbol'] = row[0]
        row_dict['variety'] = m.group(1).upper()
        dict_data.append(row_dict)
    
    if len(dict_data) == 0:
        return None
    
    return pd.DataFrame(dict_data)[output_columns]


async def async_get_dce_daily(date=None, type="future", retries=0):
    """
    异步获取大商所日交易数据
    Parameters
    ------
        date: 日期 format：YYYY-MM-DD 或 YYYYMMDD 或 datetime.date对象 为空时为当天
        type: 数据类型, 为'future'期货 或 'option'期权二者之一
        retries: 重试次数
    Return
    -------
        DataFrame 或 None
    """
    day = ct.convert_date(date) if date is not None else datetime.date.today()
    
    if retries > 3:
        print("maximum retires for DCE market data: ", day.strftime("%Y%m%d"))
        return None
    
    if type == 'future':
        params = {
            "currDate": day.strftime('%Y%m%d'),
            "year": day.strftime('%Y'),
            "month": str(int(day.strftime('%m'))-1),
            "day": day.strftime('%d')
        }
        listed_columns = ct.DCE_COLUMNS
        output_columns = ct.OUTPUT_COLUMNS
    elif type == 'option':
        params = {
            "currDate": day.strftime('%Y%m%d'),
            "year": day.strftime('%Y'),
            "month": str(int(day.strftime('%m'))-1),
            "day": day.strftime('%d'),
            "dayQuotes.trade_type": "1"
        }
        listed_columns = ct.DCE_OPTION_COLUMNS
        output_columns = ct.OPTION_OUTPUT_COLUMNS
    else:
        print('invalid type :' + type + ', should be one of "future" or "option"')
        return None

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(ct.DCE_DAILY_URL, data=params, headers=ct.DCE_HEADERS) as response:
                if response.status == 504:
                    await asyncio.sleep(1)
                    return await async_get_dce_daily(date, type, retries+1)
                elif response.status == 404:
                    return None
                elif response.status != 200:
                    print(f"DCE request failed with status {response.status}")
                    return None
                    
                response_text = await response.text(encoding='utf8')
                
    except Exception as e:
        print(f"DCE请求异常: {e}")
        await asyncio.sleep(1)
        return await async_get_dce_daily(date, type, retries+1)
    
    if u'错误：您所请求的网址（URL）无法获取' in response_text:
        await asyncio.sleep(1)
        return await async_get_dce_daily(date, type, retries+1)
    elif u'暂无数据' in response_text:
        return None
    
    data = BeautifulSoup(response_text, 'html.parser').find_all('tr')
    if len(data) == 0:
        return None
    
    dict_data = list()
    day_const = int(day.strftime('%Y%m%d'))
    
    for idata in data[1:]:
        x = idata.find_all('td')
        if len(x) == 0:
            continue
        row_data = [ix.text.strip() for ix in x]
        
        if len(row_data) < len(listed_columns):
            continue
            
        m = ct.FUTURE_SYMBOL_PATTERN.match(row_data[0])
        if not m:
            continue
            
        row_dict = {}
        for i, field in enumerate(listed_columns):
            if i < len(row_data):
                if row_data[i] == u'':
                    row_dict[field] = 0.0
                else:
                    try:
                        row_dict[field] = float(row_data[i].replace(',', ''))
                    except:
                        row_dict[field] = row_data[i]
        
        row_dict['date'] = day_const
        row_dict['symbol'] = row_data[0]
        row_dict['variety'] = m.group(1).upper()
        dict_data.append(row_dict)
    
    if len(dict_data) == 0:
        return None
    
    return pd.DataFrame(dict_data)[output_columns]


async def async_get_shfe_daily(date=None):
    """
    异步获取上期所日交易数据
    Parameters
    ------
        date: 日期 format：YYYY-MM-DD 或 YYYYMMDD 或 datetime.date对象 为空时为当天
    Return
    -------
        DataFrame 或 None
    """
    day = ct.convert_date(date) if date is not None else datetime.date.today()
    
    try:
        url = ct.SHFE_DAILY_URL % day.strftime('%Y%m%d')
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=ct.SIM_HAEDERS) as response:
                if response.status == 404:
                    return None
                json_data = await response.json()
                
    except Exception as e:
        print(f"获取上期所数据失败: {e}")
        return None
    
    if not json_data.get('o_curinstrument'):
        return None
    
    dict_data = []
    day_const = int(day.strftime('%Y%m%d'))
    
    for row in json_data['o_curinstrument']:
        if not row.get('INSTRUMENTID'):
            continue
            
        m = ct.FUTURE_SYMBOL_PATTERN.match(row['INSTRUMENTID'])
        if not m:
            continue
        
        row_dict = {
            'symbol': row['INSTRUMENTID'],
            'date': day_const,
            'open': float(row.get('OPENPRICE', 0) or 0),
            'high': float(row.get('HIGHESTPRICE', 0) or 0),
            'low': float(row.get('LOWESTPRICE', 0) or 0),
            'close': float(row.get('CLOSEPRICE', 0) or 0),
            'settle': float(row.get('SETTLEMENTPRICE', 0) or 0),
            'pre_settle': float(row.get('PRESETTLEMENTPRICE', 0) or 0),
            'volume': int(row.get('VOLUME', 0) or 0),
            'open_interest': int(row.get('OPENINTEREST', 0) or 0),
            'turnover': float(row.get('TURNOVER', 0) or 0),
            'variety': m.group(1).upper()
        }
        dict_data.append(row_dict)
    
    if len(dict_data) == 0:
        return None
    
    return pd.DataFrame(dict_data)[ct.OUTPUT_COLUMNS]


# 使用示例
async def example_usage():
    """异步使用示例"""
    # 获取中金所数据
    df1 = await async_get_cffex_daily()
    print("中金所数据:")
    print(df1.head() if df1 is not None else "无数据")
    
    # 获取郑商所数据
    df2 = await async_get_czce_daily()
    print("郑商所数据:")
    print(df2.head() if df2 is not None else "无数据")
    
    # 获取大商所数据
    df3 = await async_get_dce_daily()
    print("大商所数据:")
    print(df3.head() if df3 is not None else "无数据")
    
    # 获取上期所数据
    df4 = await async_get_shfe_daily()
    print("上期所数据:")
    print(df4.head() if df4 is not None else "无数据")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
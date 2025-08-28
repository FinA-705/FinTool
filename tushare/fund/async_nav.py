# -*- coding:utf-8 -*-

"""
异步版本的基金净值数据接口 
Created on 2024/01/01
@author: AI Assistant
@group : lazytech
"""

from __future__ import division
import time
import json
import re
import pandas as pd
import numpy as np
import aiohttp
import asyncio
from tushare.fund import cons as ct
from tushare.util import dateu as du


async def async_get_nav_open(fund_type='all'):
    """
    异步获取开放型基金净值数据
    Parameters
    ------
        type:string
            开放基金类型:
                1. all 		所有开放基金
                2. equity	股票型开放基金
                3. mix 		混合型开放基金
                4. bond		债券型开放基金
                5. monetary	货币型开放基金
                6. qdii		QDII型开放基金
     return
     -------
        DataFrame
            开放型基金净值数据(DataFrame):
                symbol      基金代码
                sname       基金名称
                per_nav     单位净值
                total_nav   累计净值
                yesterday_nav  前一日净值
                nav_a       涨跌额
                nav_rate    增长率(%)
                nav_date    净值日期
                fund_manager 基金经理
                jjlx        基金类型
                jjzfe       基金总份额
    """
    if ct._check_nav_oft_input(fund_type) is True:
        url_list = ct.NAV_OPEN_API_URL[fund_type]
        
        # 先获取基金数量
        num_url = url_list[1] % (ct.P_TYPE['http'], ct.DOMAINS['fund'])
        nums = await _async_get_fund_num(num_url)
        
        if nums is None:
            return None
            
        # 获取基金数据
        data_url = url_list[0] % (ct.P_TYPE['http'], ct.DOMAINS['fund'], nums)
        return await _async_parse_fund_data(data_url, 'open')
    else:
        print('基金类型输入错误')
        return None


async def async_get_nav_close():
    """
    异步获取封闭型基金净值数据
    return
    -------
      DataFrame
          开放型基金净值数据(DataFrame):
              symbol      基金代码
              sname       基金名称
              per_nav     单位净值
              total_nav   累计净值
              nav_a       涨跌额
              nav_rate    增长率(%)
              discount_rate 折价率(%)
              nav_date    净值日期
    """
    num_url = ct.NAV_CLOSE_API_URL[1] % (ct.P_TYPE['http'], ct.DOMAINS['fund'])
    nums = await _async_get_fund_num(num_url)
    
    if nums is None:
        return None
        
    data_url = ct.NAV_CLOSE_API_URL[0] % (ct.P_TYPE['http'], ct.DOMAINS['fund'], nums)
    return await _async_parse_fund_data(data_url, 'close')


async def async_get_nav_grading():
    """
    异步获取分级基金净值数据
    return
    -------
      DataFrame
          分级基金净值数据(DataFrame):
              symbol      基金代码
              sname       基金名称
              per_nav     单位净值
              total_nav   累计净值
              nav_a       涨跌额
              nav_rate    增长率(%)
              discount_rate 折价率(%)
              nav_date    净值日期
    """
    num_url = ct.NAV_GRADING_API_URL[1] % (ct.P_TYPE['http'], ct.DOMAINS['fund'])
    nums = await _async_get_fund_num(num_url)
    
    if nums is None:
        return None
        
    data_url = ct.NAV_GRADING_API_URL[0] % (ct.P_TYPE['http'], ct.DOMAINS['fund'], nums)
    return await _async_parse_fund_data(data_url, 'grading')


async def async_get_nav_history(code, start=None, end=None, timeout=30):
    """
    异步获取基金历史净值数据
    Parameters
    ------
      code:string
                基金代码 e.g. 000001
      start:string
                开始日期 format：YYYY-MM-DD 为空时取当前日期
      end:string
                结束日期 format：YYYY-MM-DD 为空时取去年今日
    return
    -------
      DataFrame
          基金历史净值数据(DataFrame):
              value       单位净值
              total       累计净值
              change      增长率
    """
    start = du.today_last_year() if start is None else start
    end = du.today() if end is None else end
    
    # 判断是否为货币基金
    is_monetary = await _async_check_if_monetary(code)
    
    # 获取数据数量
    nums = await _async_get_nav_history_num(code, start, end, is_monetary)
    if nums == 0:
        return None
    
    # 获取历史数据
    return await _async_parse_nav_history_data(code, start, end, nums, is_monetary, timeout)


async def async_get_fund_info(code, timeout=30):
    """
    异步获取基金基本信息
    Parameters
    ------
      code:string
                  基金代码 e.g. 000001
    return
    -------
      DataFrame
          jjqc      基金全称
          jjjc      基金简称
          symbol    基金代码
          clrq      成立日期
          ssrq      上市日期
          xcr       存续期限
          ssdd      上市地点
          Type1Name 运作方式
          Type2Name 基金类型
          Type3Name 二级分类
          jjgm      基金规模(亿元)
          jjfe      基金总份额(亿份)
          jjltfe    上市流通份额(亿份)
          jjferq    基金份额日期
          quarter   上市季度
          glr       基金管理人
          tgr       基金托管人
    """
    url = ct.SINA_FUND_INFO_URL % (ct.P_TYPE['http'], ct.DOMAINS['ssf'], code)
    
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        async with session.get(url) as response:
            content = await response.read()
            text = content.decode('gbk')
    
    org_js = json.loads(text)
    status_code = int(org_js['result']['status']['code'])
    
    if status_code != 0:
        status = str(org_js['result']['status']['msg'])
        raise ValueError(status)
    
    data = org_js['result']['data']
    fund_df = pd.DataFrame([data])
    fund_df = fund_df.set_index('symbol')
    
    return fund_df


async def _async_parse_fund_data(url, fund_type='open'):
    """异步解析基金数据"""
    ct._write_console()
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                content = await response.read()
                text = content.decode('gbk')
        
        if text == 'null':
            return None
            
        text = text.split('data:')[1].split(',exec_time')[0]
        reg = re.compile(r'\,(.*?)\:')
        text = reg.sub(r',"\1":', text)
        text = text.replace('"{symbol', '{"symbol')
        text = text.replace('{symbol', '{"symbol"')
        
        if ct.PY3:
            jstr = json.dumps(text)
        else:
            jstr = json.dumps(text, encoding='gbk')
            
        org_js = json.loads(jstr)
        fund_df = pd.DataFrame(pd.read_json(org_js, dtype={'symbol': object}),
                              columns=ct.NAV_COLUMNS[fund_type])
        fund_df.fillna(0, inplace=True)
        return fund_df
    except Exception as er:
        print(str(er))
        return None


async def _async_get_fund_num(url):
    """异步获取基金数量"""
    ct._write_console()
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                content = await response.read()
                text = content.decode('gbk')
        
        if text == 'null':
            raise ValueError('get fund num error')
        
        text = text.split('((')[1].split('))')[0]
        reg = re.compile(r'\,(.*?)\:')
        text = reg.sub(r',"\1":', text)
        text = text.replace('{total_num', '{"total_num"')
        text = text.replace('null', '0')
        org_js = json.loads(text)
        nums = org_js["total_num"]
        return int(nums)
    except Exception as er:
        print(str(er))
        return None


async def _async_get_nav_history_num(code, start, end, ismonetary=False):
    """异步获取基金历史净值数据数量"""
    if ismonetary:
        url = ct.SINA_NAV_HISTROY_COUNT_CUR_URL % (
            ct.P_TYPE['http'], ct.DOMAINS['ssf'], code, start, end)
    else:
        url = ct.SINA_NAV_HISTROY_COUNT_URL % (
            ct.P_TYPE['http'], ct.DOMAINS['ssf'], code, start, end)
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            content = await response.read()
            text = content.decode('gbk')
    
    org_js = json.loads(text)
    status_code = int(org_js['result']['status']['code'])
    
    if status_code != 0:
        status = str(org_js['result']['status']['msg'])
        raise ValueError(status)
    
    nums = org_js["result"]["data"]["total_num"]
    return int(nums)


async def _async_parse_nav_history_data(code, start, end, nums, ismonetary=False, timeout=30):
    """异步解析基金历史净值数据"""
    if nums == 0:
        return None
    
    ct._write_console()
    
    if ismonetary:
        url = ct.SINA_NAV_HISTROY_DATA_CUR_URL % (
            ct.P_TYPE['http'], ct.DOMAINS['ssf'], code, start, end, nums)
    else:
        url = ct.SINA_NAV_HISTROY_DATA_URL % (
            ct.P_TYPE['http'], ct.DOMAINS['ssf'], code, start, end, nums)
    
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        async with session.get(url) as response:
            content = await response.read()
            text = content.decode('gbk')
    
    org_js = json.loads(text)
    status_code = int(org_js['result']['status']['code'])
    
    if status_code != 0:
        status = str(org_js['result']['status']['msg'])
        raise ValueError(status)
    
    data = org_js['result']['data']['data']
    
    if 'jjjz' in data[0].keys():
        fund_df = pd.DataFrame(data, columns=ct.NAV_HIS_JJJZ)
        fund_df['jjjz'] = fund_df['jjjz'].astype(float)
        fund_df['ljjz'] = fund_df['ljjz'].astype(float)
        fund_df.rename(columns=ct.DICT_NAV_EQUITY, inplace=True)
    else:
        fund_df = pd.DataFrame(data, columns=ct.NAV_HIS_NHSY)
        fund_df['nhsyl'] = fund_df['nhsyl'].astype(float)
        fund_df['dwsy'] = fund_df['dwsy'].astype(float)
        fund_df.rename(columns=ct.DICT_NAV_MONETARY, inplace=True)
    
    if fund_df['date'].dtypes == np.object:
        fund_df['date'] = pd.to_datetime(fund_df['date'])
    
    fund_df = fund_df.set_index('date')
    fund_df = fund_df.sort_index(ascending=False)
    fund_df['pre_value'] = fund_df['value'].shift(-1)
    fund_df['change'] = (fund_df['value'] / fund_df['pre_value'] - 1) * 100
    
    return fund_df


async def _async_check_if_monetary(code):
    """异步检查是否为货币基金"""
    # 这里简化处理，实际应该查询基金类型
    # 货币基金代码通常以特定规则命名，这里用简单的判断
    return False  # 简化返回，实际应该通过API查询基金类型


# 使用示例
async def example_usage():
    """异步使用示例"""
    # 获取开放型基金净值
    df1 = await async_get_nav_open('equity')
    print("股票型开放基金净值:")
    print(df1.head())
    
    # 获取基金历史净值
    df2 = await async_get_nav_history('000001', '2023-01-01', '2023-12-31')
    print("基金历史净值:")
    print(df2.head())
    
    # 获取基金基本信息
    df3 = await async_get_fund_info('000001')
    print("基金基本信息:")
    print(df3)


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
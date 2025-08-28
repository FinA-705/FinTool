# -*- coding:utf-8 -*- 
"""
异步版本的电影票房数据模块
Created on 2024/01/01
@author: AI Assistant
@group : waditu
"""
import pandas as pd
import aiohttp
import asyncio
import json
import time
from tushare.stock import cons as ct
from tushare.util import dateu as du


def _random(n=13):
    """生成随机数"""
    from random import randint
    start = 10**(n-1)
    end = (10**n)-1
    return randint(start, end)


async def async_realtime_boxoffice():
    """
    异步获取实时电影票房数据
    数据来源：EBOT艺恩票房智库
     return
     -------
        DataFrame 
              BoxOffice     实时票房（万） 
              Irank         排名
              MovieName     影片名 
              boxPer        票房占比 （%）
              movieDay      上映天数
              sumBoxOffice  累计票房（万） 
              time          数据获取时间
    """
    try:
        url = ct.MOVIE_BOX % (ct.P_TYPE['http'], ct.DOMAINS['mbox'], ct.BOX, _random())
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                content = await response.read()
                
        if len(content) < 15:  # no data
            return None
            
        js = json.loads(content.decode('utf-8'))
        df = pd.DataFrame(js['data2'])
        df = df.drop(['MovieImg','mId'], axis=1)
        df['time'] = du.get_now()
        return df
        
    except Exception as e:
        print(f"获取实时票房数据失败: {e}")
        return None


async def async_day_boxoffice(date=None):
    """
    异步获取单日电影票房数据
    数据来源：EBOT艺恩票房智库
    Parameters
    ------
        date:日期，默认为上一日
     return
     -------
        DataFrame 
              AvgPrice      平均票价
              AvpPeoPle     场均人次
              BoxOffice     单日票房（万）
              BoxOffice_Up  环比变化 （%）
              IRank         排名
              MovieDay      上映天数
              MovieName     影片名 
              SumBoxOffice  累计票房（万） 
              WomIndex      口碑指数 
    """
    try:
        if date is None:
            date = 0
        else:
            date = int(du.diff_day(du.today(), date)) + 1
            
        url = ct.BOXOFFICE_DAY % (ct.P_TYPE['http'], ct.DOMAINS['mbox'], ct.BOX, date, _random())
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                content = await response.read()
                
        if len(content) < 15:  # no data
            return None
            
        js = json.loads(content.decode('utf-8'))
        df = pd.DataFrame(js['data1'])
        df = df.drop(['MovieImg', 'BoxOffice1', 'MovieID', 'Director', 'IRank_pro'], axis=1)
        return df
        
    except Exception as e:
        print(f"获取单日票房数据失败: {e}")
        return None


async def async_month_boxoffice(date=None):
    """
    异步获取月度电影票房数据
    数据来源：EBOT艺恩票房智库
    Parameters
    ------
        date: 日期（月份），默认为当前月份
    return
    -------
        DataFrame
            月度票房数据
    """
    try:
        if date is None:
            date = 0
        else:
            # 计算月份差异
            today = du.today()
            date_obj = du.to_date(date)
            months_diff = (today.year - date_obj.year) * 12 + today.month - date_obj.month
            date = months_diff
            
        url = ct.BOXOFFICE_MONTH % (ct.P_TYPE['http'], ct.DOMAINS['mbox'], ct.BOX, date, _random())
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                content = await response.read()
                
        if len(content) < 15:  # no data
            return None
            
        js = json.loads(content.decode('utf-8'))
        df = pd.DataFrame(js['data1'])
        # 根据实际返回的数据结构调整列处理
        return df
        
    except Exception as e:
        print(f"获取月度票房数据失败: {e}")
        return None


async def async_day_cinema(date=None):
    """
    异步获取单日影院票房数据
    数据来源：EBOT艺恩票房智库
    Parameters
    ------
        date: 日期，默认为上一日
    return
    -------
        DataFrame
            影院票房数据
    """
    try:
        if date is None:
            date = 0
        else:
            date = int(du.diff_day(du.today(), date)) + 1
        
        all_data = []
        page = 1
        
        while True:
            df = await _async_day_cinema(date, page)
            if df is None or len(df) == 0:
                break
            all_data.append(df)
            page += 1
            await asyncio.sleep(0.1)  # 避免请求过快
            
        if not all_data:
            return None
            
        data = pd.concat(all_data, ignore_index=True)
        data = data.drop_duplicates()
        return data.reset_index(drop=True)
        
    except Exception as e:
        print(f"获取影院票房数据失败: {e}")
        return None


async def _async_day_cinema(date=None, pNo=1):
    """异步获取单页影院数据"""
    try:
        url = ct.BOXOFFICE_CBD % (ct.P_TYPE['http'], ct.DOMAINS['mbox'], ct.BOX, pNo, date)
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                content = await response.read()
                
        if len(content) < 15:  # no data
            return None
            
        js = json.loads(content.decode('utf-8'))
        df = pd.DataFrame(js['data1'])
        df = df.drop(['CinemaID'], axis=1)
        return df
        
    except Exception as e:
        print(f"获取单页影院数据失败: {e}")
        return None


async def async_get_movie_rankings(date=None, ranking_type='day'):
    """
    异步获取电影排行榜数据
    Parameters
    ------
        date: 日期
        ranking_type: 排行类型 ('day', 'week', 'month')
    return
    -------
        DataFrame
            电影排行数据
    """
    try:
        if date is None:
            date = 0
        else:
            if ranking_type == 'day':
                date = int(du.diff_day(du.today(), date)) + 1
            elif ranking_type == 'week':
                date = int(du.diff_day(du.today(), date) / 7)
            elif ranking_type == 'month':
                today = du.today()
                date_obj = du.to_date(date)
                date = (today.year - date_obj.year) * 12 + today.month - date_obj.month
        
        # 根据排行类型选择不同的URL
        if ranking_type == 'day':
            url = ct.BOXOFFICE_DAY % (ct.P_TYPE['http'], ct.DOMAINS['mbox'], ct.BOX, date, _random())
        elif ranking_type == 'week':
            url = ct.BOXOFFICE_WEEK % (ct.P_TYPE['http'], ct.DOMAINS['mbox'], ct.BOX, date, _random())
        elif ranking_type == 'month':
            url = ct.BOXOFFICE_MONTH % (ct.P_TYPE['http'], ct.DOMAINS['mbox'], ct.BOX, date, _random())
        else:
            raise ValueError("ranking_type must be one of 'day', 'week', 'month'")
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                content = await response.read()
                
        if len(content) < 15:  # no data
            return None
            
        js = json.loads(content.decode('utf-8'))
        df = pd.DataFrame(js['data1'])
        return df
        
    except Exception as e:
        print(f"获取电影排行数据失败: {e}")
        return None


# 使用示例
async def example_usage():
    """异步使用示例"""
    # 获取实时票房
    df1 = await async_realtime_boxoffice()
    print("实时票房:")
    print(df1.head() if df1 is not None else "无数据")
    
    # 获取单日票房
    df2 = await async_day_boxoffice()
    print("单日票房:")
    print(df2.head() if df2 is not None else "无数据")
    
    # 获取月度票房
    df3 = await async_month_boxoffice()
    print("月度票房:")
    print(df3.head() if df3 is not None else "无数据")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
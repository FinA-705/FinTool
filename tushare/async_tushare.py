#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
TuShare异步版本总入口模块
Created on 2024/01/01
@author: AI Assistant
@group : waditu

这个模块提供了TuShare库的异步版本，支持高并发的数据获取。
所有的异步函数都使用aiohttp库进行HTTP请求，可以大幅提升数据获取效率。

使用方式:
    import asyncio
    import tushare.async_tushare as ats
    
    async def main():
        # 获取实时行情
        df = await ats.async_get_realtime_quotes(['000001', '000002'])
        print(df)
    
    asyncio.run(main())
"""

# 导入所有异步模块
from tushare.pro.client import AsyncDataApi
from tushare.pro.llm import AsyncGPTClient
from tushare.pro.async_data_pro import (
    async_pro_api, async_pro_bar, async_pro_bar_vip,
    async_batch_pro_bar, async_multi_asset_data,
    async_subs, async_ht_subs
)
from tushare.util.netbase import AsyncClient
from tushare.util.common import AsyncClient as AsyncCommonClient
from tushare.util.verify_token import async_verify_token
from tushare.trader.trader import AsyncTraderAPI

# 导入异步股票数据模块
from tushare.stock.async_histroy_divide import (
    async_realtime_tick,
    async_get_stock_tx_a_divide_amount,
    async_get_stock_sina_a_divide_amount,
    async_get_stock_dc_a_divide_amount
)

from tushare.stock.async_rtq import (
    async_get_realtime_quotes,
    async_get_today_all,
    async_get_stock_basics,
    async_get_sina_dd
)

# 导入异步基金数据模块
from tushare.fund.async_nav import (
    async_get_nav_open,
    async_get_nav_close,
    async_get_nav_grading,
    async_get_nav_history,
    async_get_fund_info
)

# 导入异步期货数据模块
from tushare.futures.async_domestic import (
    async_get_cffex_daily,
    async_get_czce_daily,
    async_get_dce_daily,
    async_get_shfe_daily
)

# 导入异步互联网数据模块
from tushare.internet.async_boxoffice import (
    async_realtime_boxoffice,
    async_day_boxoffice,
    async_month_boxoffice,
    async_day_cinema,
    async_get_movie_rankings
)

import asyncio
import pandas as pd
from typing import List, Union, Optional


class AsyncTuShare:
    """
    TuShare异步版本的主要接口类
    
    这个类封装了所有的异步数据获取方法，提供统一的接口。
    """
    
    def __init__(self, token: str = None):
        """
        初始化AsyncTuShare
        
        Parameters
        ----------
        token : str, optional
            TuShare Pro的token，用于访问付费数据
        """
        self.token = token
        self._pro_api = AsyncDataApi(token) if token else None
        self._gpt_client = AsyncGPTClient(token) if token else None
        self._trader_api = None
    
    # Pro数据接口
    async def pro_query(self, api_name: str, fields: str = '', **kwargs) -> pd.DataFrame:
        """
        异步查询TuShare Pro数据
        
        Parameters
        ----------
        api_name : str
            API接口名称
        fields : str
            需要获取的字段，用逗号分隔
        **kwargs
            其他查询参数
            
        Returns
        -------
        DataFrame
            查询结果
        """
        if not self._pro_api:
            raise ValueError("需要提供token才能使用Pro接口")
        return await self._pro_api.query(api_name, fields, **kwargs)
    
    async def pro_bar(self, ts_code: str = '', start_date: str = '', end_date: str = '', 
                     freq: str = 'D', asset: str = 'E', **kwargs) -> pd.DataFrame:
        """
        异步获取BAR数据
        
        Parameters
        ----------
        ts_code : str
            证券代码
        start_date : str
            开始日期
        end_date : str
            结束日期
        freq : str
            频率，默认日线
        asset : str
            资产类型，默认股票
        **kwargs
            其他参数
            
        Returns
        -------
        DataFrame
            BAR数据
        """
        api = self._pro_api if self._pro_api else async_pro_api(self.token)
        return await async_pro_bar(ts_code=ts_code, api=api, start_date=start_date, 
                                  end_date=end_date, freq=freq, asset=asset, **kwargs)
    
    async def pro_bar_vip(self, ts_code: str = '', start_date: str = '', end_date: str = '', 
                         freq: str = 'D', asset: str = 'E', **kwargs) -> pd.DataFrame:
        """
        异步获取VIP版本的BAR数据
        
        Parameters
        ----------
        ts_code : str
            证券代码
        start_date : str
            开始日期
        end_date : str
            结束日期
        freq : str
            频率，默认日线
        asset : str
            资产类型，默认股票
        **kwargs
            其他参数
            
        Returns
        -------
        DataFrame
            VIP BAR数据
        """
        api = self._pro_api if self._pro_api else async_pro_api(self.token)
        return await async_pro_bar_vip(ts_code=ts_code, api=api, start_date=start_date, 
                                      end_date=end_date, freq=freq, asset=asset, **kwargs)
    
    async def batch_pro_bar(self, ts_codes_list: List[str], **kwargs) -> dict:
        """
        批量异步获取多只股票的BAR数据
        
        Parameters
        ----------
        ts_codes_list : List[str]
            股票代码列表
        **kwargs
            其他pro_bar参数
            
        Returns
        -------
        dict
            以股票代码为key，DataFrame为value的字典
        """
        # 为每个请求设置API
        if 'api' not in kwargs:
            kwargs['api'] = self._pro_api if self._pro_api else async_pro_api(self.token)
        
        return await async_batch_pro_bar(ts_codes_list, **kwargs)
    
    async def multi_asset_data(self, requests_list: List[dict]) -> List[pd.DataFrame]:
        """
        异步获取多种资产类型的数据
        
        Parameters
        ----------
        requests_list : List[dict]
            请求列表，每个元素包含参数字典
            
        Returns
        -------
        List[DataFrame]
            结果列表
        """
        # 为每个请求设置API
        for request in requests_list:
            if 'api' not in request:
                request['api'] = self._pro_api if self._pro_api else async_pro_api(self.token)
        
        return await async_multi_asset_data(requests_list)
    
    # GPT接口
    async def gpt_query(self, model: str, messages: List[dict], **kwargs) -> dict:
        """
        异步查询GPT
        
        Parameters
        ----------
        model : str
            模型名称
        messages : List[dict]
            对话消息列表
        **kwargs
            其他参数
            
        Returns
        -------
        dict
            GPT响应结果
        """
        if not self._gpt_client:
            raise ValueError("需要提供token才能使用GPT接口")
        return await self._gpt_client.gpt_query(model, messages, **kwargs)
    
    async def gpt_stream(self, model: str, messages: List[dict], **kwargs):
        """
        异步流式查询GPT
        
        Parameters
        ----------
        model : str
            模型名称
        messages : List[dict]
            对话消息列表
        **kwargs
            其他参数
            
        Yields
        ------
        dict
            GPT流式响应
        """
        if not self._gpt_client:
            raise ValueError("需要提供token才能使用GPT接口")
        async for chunk in self._gpt_client.gpt_stream(model, messages, **kwargs):
            yield chunk
    
    # 股票数据接口
    async def get_realtime_quotes(self, symbols: Union[str, List[str]]) -> pd.DataFrame:
        """
        异步获取实时行情数据
        
        Parameters
        ----------
        symbols : str or List[str]
            股票代码或代码列表
            
        Returns
        -------
        DataFrame
            实时行情数据
        """
        return await async_get_realtime_quotes(symbols)
    
    async def get_realtime_tick(self, ts_code: str, src: str = "tx", page_count: int = None) -> pd.DataFrame:
        """
        异步获取历史分笔数据
        
        Parameters
        ----------
        ts_code : str
            股票代码
        src : str
            数据源
        page_count : int
            页数限制
            
        Returns
        -------
        DataFrame
            历史分笔数据
        """
        return await async_realtime_tick(ts_code, src, page_count)
    
    async def get_stock_basics(self) -> pd.DataFrame:
        """
        异步获取股票基本信息
        
        Returns
        -------
        DataFrame
            股票基本信息
        """
        return await async_get_stock_basics()
    
    # 基金数据接口
    async def get_nav_open(self, fund_type: str = 'all') -> pd.DataFrame:
        """
        异步获取开放型基金净值数据
        
        Parameters
        ----------
        fund_type : str
            基金类型
            
        Returns
        -------
        DataFrame
            基金净值数据
        """
        return await async_get_nav_open(fund_type)
    
    async def get_nav_history(self, code: str, start: str = None, end: str = None) -> pd.DataFrame:
        """
        异步获取基金历史净值数据
        
        Parameters
        ----------
        code : str
            基金代码
        start : str
            开始日期
        end : str
            结束日期
            
        Returns
        -------
        DataFrame
            基金历史净值数据
        """
        return await async_get_nav_history(code, start, end)
    
    async def get_fund_info(self, code: str) -> pd.DataFrame:
        """
        异步获取基金基本信息
        
        Parameters
        ----------
        code : str
            基金代码
            
        Returns
        -------
        DataFrame
            基金基本信息
        """
        return await async_get_fund_info(code)
    
    # 期货数据接口
    async def get_cffex_daily(self, date: str = None) -> pd.DataFrame:
        """
        异步获取中金所日交易数据
        
        Parameters
        ----------
        date : str
            交易日期
            
        Returns
        -------
        DataFrame
            中金所交易数据
        """
        return await async_get_cffex_daily(date)
    
    async def get_czce_daily(self, date: str = None, type: str = "future") -> pd.DataFrame:
        """
        异步获取郑商所日交易数据
        
        Parameters
        ----------
        date : str
            交易日期
        type : str
            数据类型
            
        Returns
        -------
        DataFrame
            郑商所交易数据
        """
        return await async_get_czce_daily(date, type)
    
    async def get_dce_daily(self, date: str = None, type: str = "future") -> pd.DataFrame:
        """
        异步获取大商所日交易数据
        
        Parameters
        ----------
        date : str
            交易日期
        type : str
            数据类型
            
        Returns
        -------
        DataFrame
            大商所交易数据
        """
        return await async_get_dce_daily(date, type)
    
    async def get_shfe_daily(self, date: str = None) -> pd.DataFrame:
        """
        异步获取上期所日交易数据
        
        Parameters
        ----------
        date : str
            交易日期
            
        Returns
        -------
        DataFrame
            上期所交易数据
        """
        return await async_get_shfe_daily(date)
    
    # 互联网数据接口
    async def get_realtime_boxoffice(self) -> pd.DataFrame:
        """
        异步获取实时电影票房数据
        
        Returns
        -------
        DataFrame
            实时票房数据
        """
        return await async_realtime_boxoffice()
    
    async def get_day_boxoffice(self, date: str = None) -> pd.DataFrame:
        """
        异步获取单日电影票房数据
        
        Parameters
        ----------
        date : str
            日期
            
        Returns
        -------
        DataFrame
            单日票房数据
        """
        return await async_day_boxoffice(date)
    
    # 交易接口
    def init_trader(self, broker: str):
        """
        初始化交易接口
        
        Parameters
        ----------
        broker : str
            券商代码
        """
        self._trader_api = AsyncTraderAPI(broker)
        return self._trader_api
    
    # 批量数据获取
    async def batch_get_quotes(self, symbols_list: List[List[str]]) -> List[pd.DataFrame]:
        """
        批量异步获取多组股票行情数据
        
        Parameters
        ----------
        symbols_list : List[List[str]]
            股票代码组列表
            
        Returns
        -------
        List[DataFrame]
            行情数据列表
        """
        tasks = []
        for symbols in symbols_list:
            task = self.get_realtime_quotes(symbols)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
    
    async def batch_get_fund_data(self, codes: List[str]) -> List[pd.DataFrame]:
        """
        批量异步获取基金信息
        
        Parameters
        ----------
        codes : List[str]
            基金代码列表
            
        Returns
        -------
        List[DataFrame]
            基金信息列表
        """
        tasks = []
        for code in codes:
            task = self.get_fund_info(code)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]


# 全局实例
default_async_ts = AsyncTuShare()

# 便捷函数
async def get_realtime_quotes(symbols: Union[str, List[str]]) -> pd.DataFrame:
    """便捷函数：异步获取实时行情"""
    return await default_async_ts.get_realtime_quotes(symbols)

async def get_realtime_tick(ts_code: str, src: str = "tx", page_count: int = None) -> pd.DataFrame:
    """便捷函数：异步获取历史分笔数据"""
    return await default_async_ts.get_realtime_tick(ts_code, src, page_count)

async def get_nav_open(fund_type: str = 'all') -> pd.DataFrame:
    """便捷函数：异步获取开放型基金净值"""
    return await default_async_ts.get_nav_open(fund_type)

async def get_realtime_boxoffice() -> pd.DataFrame:
    """便捷函数：异步获取实时票房"""
    return await default_async_ts.get_realtime_boxoffice()

async def pro_bar(ts_code: str = '', start_date: str = '', end_date: str = '', 
                 freq: str = 'D', asset: str = 'E', **kwargs) -> pd.DataFrame:
    """便捷函数：异步获取BAR数据"""
    return await default_async_ts.pro_bar(ts_code, start_date, end_date, freq, asset, **kwargs)

async def pro_bar_vip(ts_code: str = '', start_date: str = '', end_date: str = '', 
                     freq: str = 'D', asset: str = 'E', **kwargs) -> pd.DataFrame:
    """便捷函数：异步获取VIP BAR数据"""
    return await default_async_ts.pro_bar_vip(ts_code, start_date, end_date, freq, asset, **kwargs)

async def batch_pro_bar(ts_codes_list: List[str], **kwargs) -> dict:
    """便捷函数：批量异步获取BAR数据"""
    return await default_async_ts.batch_pro_bar(ts_codes_list, **kwargs)


# 使用示例
async def example_usage():
    """使用示例"""
    # 创建异步TuShare实例
    ats = AsyncTuShare()
    
    print("=== 异步TuShare使用示例 ===")
    
    # 1. 获取实时行情
    print("1. 获取实时行情...")
    try:
        quotes = await ats.get_realtime_quotes(['000001', '000002'])
        print(f"获取到 {len(quotes)} 条行情数据")
        print(quotes.head())
    except Exception as e:
        print(f"获取行情失败: {e}")
    
    # 2. 获取基金数据
    print("\n2. 获取基金数据...")
    try:
        nav_data = await ats.get_nav_open('equity')
        print(f"获取到 {len(nav_data)} 条基金数据")
        print(nav_data.head())
    except Exception as e:
        print(f"获取基金数据失败: {e}")
    
    # 3. 获取票房数据
    print("\n3. 获取票房数据...")
    try:
        boxoffice = await ats.get_realtime_boxoffice()
        if boxoffice is not None:
            print(f"获取到 {len(boxoffice)} 条票房数据")
            print(boxoffice.head())
        else:
            print("暂无票房数据")
    except Exception as e:
        print(f"获取票房数据失败: {e}")
    
    # 4. 批量获取数据
    print("\n4. 批量获取数据...")
    try:
        symbols_groups = [['000001', '000002'], ['600000', '600001']]
        batch_results = await ats.batch_get_quotes(symbols_groups)
        print(f"批量获取了 {len(batch_results)} 组数据")
    except Exception as e:
        print(f"批量获取失败: {e}")
    
    # 5. Pro BAR数据
    print("\n5. 获取Pro BAR数据...")
    try:
        # 需要有效的token
        if ats.token:
            bar_data = await ats.pro_bar(ts_code='000001.SZ', start_date='20231201', end_date='20231231')
            if bar_data is not None:
                print(f"获取到 {len(bar_data)} 条BAR数据")
                print(bar_data.head())
            else:
                print("暂无BAR数据")
        else:
            print("需要token才能使用Pro接口")
    except Exception as e:
        print(f"获取BAR数据失败: {e}")
    
    # 6. 批量获取BAR数据
    print("\n6. 批量获取BAR数据...")
    try:
        if ats.token:
            ts_codes = ['000001.SZ', '000002.SZ', '600000.SH']
            batch_bar_data = await ats.batch_pro_bar(ts_codes, start_date='20231201', end_date='20231231')
            
            success_count = sum(1 for v in batch_bar_data.values() if v is not None)
            print(f"批量BAR获取完成: {success_count}/{len(ts_codes)} 成功")
        else:
            print("需要token才能使用Pro接口")
    except Exception as e:
        print(f"批量获取BAR数据失败: {e}")


if __name__ == "__main__":
    # 运行示例
    print("TuShare异步版本模块")
    print("支持的主要功能：")
    print("- 异步股票行情数据获取")
    print("- 异步基金数据获取")
    print("- 异步期货数据获取")
    print("- 异步互联网数据获取")
    print("- Pro数据接口（需要token）")
    print("- Pro BAR数据接口（需要token）")
    print("- VIP版本数据接口（需要token）")
    print("- GPT接口（需要token）")
    print("- 批量数据获取")
    print("- 多资产类型数据获取")
    print("\n运行示例...")
    
    asyncio.run(example_usage())
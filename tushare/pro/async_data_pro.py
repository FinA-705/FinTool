# -*- coding:utf-8 -*- 
"""
异步版本的 pro data_pro 模块
Created on 2024/01/01
@author: AI Assistant
@group : https://tushare.pro
"""
from __future__ import division
import datetime
import asyncio
from tushare.pro.client import AsyncDataApi
from tushare.util import upass
from tushare.util.formula import MA

PRICE_COLS = ['open', 'close', 'high', 'low', 'pre_close']
FORMAT = lambda x: '%.2f' % x
FREQS = {'D': '1DAY',
         'W': '1WEEK',
         'Y': '1YEAR',
         }
FACT_LIST = {
           'tor': 'turnover_rate',
           'turnover_rate': 'turnover_rate',
           'vr': 'volume_ratio',
           'volume_ratio': 'volume_ratio',
           'pe': 'pe',
           'pe_ttm': 'pe_ttm',
        }


def async_pro_api(token='', timeout=30):
    """
    异步初始化pro API,第一次可以通过ts.set_token('your token')来记录自己的token凭证，临时token可以通过本参数传入
    """
    if token == '' or token is None:
        token = upass.get_token()
    if token is not None and token != '':
        pro = AsyncDataApi(token=token, timeout=timeout)
        return pro
    else:
        raise Exception('api init error.')


async def async_pro_bar(ts_code='', api=None, start_date='', end_date='', freq='D', asset='E',
                       exchange='',
                       adj=None,
                       ma=[],
                       factors=None,
                       adjfactor=False,
                       offset=None,
                       limit=None,
                       fields='',
                       contract_type='',
                       retry_count=3):
    """
    异步获取BAR数据
    Parameters:
    ------------
    ts_code:证券代码，支持股票,ETF/LOF,期货/期权,港股,数字货币
    start_date:开始日期  YYYYMMDD
    end_date:结束日期 YYYYMMDD
    freq:支持1/5/15/30/60分钟,周/月/季/年
    asset:证券类型 E:股票和交易所基金，I:沪深指数,C:数字货币,FT:期货 FD:基金/O期权/H港股/CB可转债
    exchange:市场代码，用户数字货币行情
    adj:复权类型,None不复权,qfq:前复权,hfq:后复权
    ma:均线,支持自定义均线频度，如：ma5/ma10/ma20/ma60/maN
    offset:开始行数（分页功能，从第几行开始取数据）
    limit: 本次提取数据行数
    factors因子数据，目前支持以下两种：
        vr:量比,默认不返回，返回需指定：factor=['vr']
        tor:换手率，默认不返回，返回需指定：factor=['tor']
                    以上两种都需要：factor=['vr', 'tor']
    retry_count:网络重试次数

    Return
    ----------
    DataFrame
    code:代码
    open：开盘close/high/low/vol成交量/amount成交额/maN均价/vr量比/tor换手率

         期货(asset='FT')
    code/open/close/high/low/avg_price：均价  position：持仓量  vol：成交总量
    """
    if (ts_code == '' or ts_code is None) and (adj is not None):
        print('提取复权行情必须输入ts_code参数')
        return

    if len(freq.strip()) >= 3:
        freq = freq.strip().lower()
    else:
        freq = freq.strip().upper() if asset != 'C' else freq.strip().lower()

    if 'min' not in freq:
        today = datetime.datetime.today().date()
        today = str(today)[0:10]
        start_date = '' if start_date is None else start_date
        end_date = today if end_date == '' or end_date is None else end_date
        start_date = start_date.replace('-', '')
        end_date = end_date.replace('-', '')

    ts_code = ts_code.strip().upper() if asset != 'C' else ts_code.strip().lower()
    asset = asset.strip().upper()
    api = api if api is not None else async_pro_api()

    for attempt in range(retry_count):
        try:
            data = None
            
            if asset == 'E':
                if freq == 'D':
                    data = await api.daily(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                    if factors is not None and len(factors) > 0:
                        ds = await api.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
                        ds = ds[['trade_date', 'turnover_rate', 'volume_ratio']]
                        ds = ds.set_index('trade_date')
                        data = data.set_index('trade_date')
                        data = data.merge(ds, left_index=True, right_index=True)
                        data = data.reset_index()
                        if ('tor' in factors) and ('vr' not in factors):
                            data = data.drop('volume_ratio', axis=1)
                        if ('vr' in factors) and ('tor' not in factors):
                            data = data.drop('turnover_rate', axis=1)
                elif freq == 'W':
                    data = await api.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif freq == 'M':
                    data = await api.monthly(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.stk_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)
                    data['trade_date'] = data['trade_time'].map(lambda x: x.replace('-', '')[0:8])
                    data['pre_close'] = data['close'].shift(-1)

                if adj is not None:
                    fcts = await api.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)
                    fcts = fcts[['trade_date', 'adj_factor']]
                    if fcts.shape[0] == 0:
                        return None
                    data = data.set_index('trade_date', drop=False).merge(fcts.set_index('trade_date'), left_index=True, right_index=True, how='left')
                    if 'min' in freq:
                        data = data.sort_values('trade_time', ascending=False)
                    data['adj_factor'] = data['adj_factor'].fillna(method='bfill')
                    for col in PRICE_COLS:
                        if adj == 'hfq':
                            data[col] = data[col] * data['adj_factor']
                        if adj == 'qfq':
                            data[col] = data[col] * data['adj_factor'] / float(fcts['adj_factor'].iloc[0])
                        data[col] = data[col].map(FORMAT)
                        data[col] = data[col].astype(float)
                    if adjfactor is False:
                        data = data.drop('adj_factor', axis=1)
                    if 'min' not in freq:
                        data['change'] = data['close'] - data['pre_close']
                        data['pct_chg'] = data['change'] / data['pre_close'] * 100
                        data['pct_chg'] = data['pct_chg'].map(lambda x: FORMAT(x)).astype(float)
                    else:
                        data = data.drop(['trade_date', 'pre_close'], axis=1)
                else:
                    data['pre_close'] = data['close'].shift(-1)
                    data['change'] = data['close'] - data['pre_close']
                    data['pct_chg'] = data['change'] / data['pre_close'] * 100
                    data['pct_chg'] = data['pct_chg'].map(lambda x: FORMAT(x)).astype(float)

            elif asset == 'I':
                if freq == 'D':
                    data = await api.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif freq == 'W':
                    data = await api.index_weekly(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif freq == 'M':
                    data = await api.index_monthly(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.stk_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)

            elif asset == 'FT':
                if freq == 'D':
                    data = await api.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, exchange=exchange, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.ft_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)

            elif asset == 'O':
                if freq == 'D':
                    data = await api.opt_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, exchange=exchange, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.opt_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)

            elif asset == 'CB':
                if freq == 'D':
                    data = await api.cb_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)

            elif asset == 'FD':
                if freq == 'D':
                    data = await api.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.stk_mins(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)

            elif asset == 'C':
                if freq == 'd':
                    freq = 'daily'
                elif freq == 'w':
                    freq = 'week'
                data = await api.coinbar(exchange=exchange, symbol=ts_code, freq=freq, start_date=start_date, end_date=end_date,
                                       contract_type=contract_type)

            # 计算均线
            if data is not None and ma is not None and len(ma) > 0:
                for a in ma:
                    if isinstance(a, int):
                        data['ma%s' % a] = MA(data['close'], a).map(FORMAT).shift(-(a-1))
                        data['ma%s' % a] = data['ma%s' % a].astype(float)
                        data['ma_v_%s' % a] = MA(data['vol'], a).map(FORMAT).shift(-(a-1))
                        data['ma_v_%s' % a] = data['ma_v_%s' % a].astype(float)

            if data is not None:
                data = data.reset_index(drop=True)

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)  # 异步等待重试
        else:
            if data is not None:
                if fields is not None and fields != '':
                    f_list = [col.strip() for col in fields.split(',')]
                    data = data[f_list]
                return data

    raise IOError('ERROR: All retry attempts failed.')


async def async_pro_bar_vip(ts_code='', api=None, start_date='', end_date='', freq='D', asset='E',
                           exchange='',
                           adj=None,
                           ma=[],
                           factors=None,
                           adjfactor=False,
                           offset=None,
                           limit=None,
                           fields='',
                           contract_type='',
                           retry_count=3):
    """
    异步获取VIP版本的BAR数据
    Parameters:
    ------------
    ts_code:证券代码，支持股票,ETF/LOF,期货/期权,港股,数字货币
    start_date:开始日期  YYYYMMDD
    end_date:结束日期 YYYYMMDD
    freq:支持1/5/15/30/60分钟,周/月/季/年
    asset:证券类型 E:股票和交易所基金，I:沪深指数,C:数字货币,FT:期货 FD:基金/O期权/H港股/CB可转债
    exchange:市场代码，用户数字货币行情
    adj:复权类型,None不复权,qfq:前复权,hfq:后复权
    ma:均线,支持自定义均线频度，如：ma5/ma10/ma20/ma60/maN
    offset:开始行数（分页功能，从第几行开始取数据）
    limit: 本次提取数据行数
    factors因子数据，目前支持以下两种：
        vr:量比,默认不返回，返回需指定：factor=['vr']
        tor:换手率，默认不返回，返回需指定：factor=['tor']
                    以上两种都需要：factor=['vr', 'tor']
    retry_count:网络重试次数
    
    Return
    ----------
    DataFrame
    code:代码
    open：开盘close/high/low/vol成交量/amount成交额/maN均价/vr量比/tor换手率
    
         期货(asset='FT')
    code/open/close/high/low/avg_price：均价  position：持仓量  vol：成交总量
    """
    if (ts_code == '' or ts_code is None) and (adj is not None):
        print('提取复权行情必须输入ts_code参数')
        return

    if len(freq.strip()) >= 3:
        freq = freq.strip().lower()
    else:
        freq = freq.strip().upper() if asset != 'C' else freq.strip().lower()
        
    if 'min' not in freq:
        today = datetime.datetime.today().date()
        today = str(today)[0:10]
        start_date = '' if start_date is None else start_date
        end_date = today if end_date == '' or end_date is None else end_date
        start_date = start_date.replace('-', '')
        end_date = end_date.replace('-', '')

    ts_code = ts_code.strip().upper() if asset != 'C' else ts_code.strip().lower()
    asset = asset.strip().upper()
    api = api if api is not None else async_pro_api()

    for attempt in range(retry_count):
        try:
            data = None
            
            if asset == 'E':
                if freq == 'D':
                    data = await api.daily_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                    if factors is not None and len(factors) > 0:
                        ds = await api.daily_basic_vip(ts_code=ts_code, start_date=start_date, end_date=end_date)
                        ds = ds[['trade_date', 'turnover_rate', 'volume_ratio']]
                        ds = ds.set_index('trade_date')
                        data = data.set_index('trade_date')
                        data = data.merge(ds, left_index=True, right_index=True)
                        data = data.reset_index()
                        if ('tor' in factors) and ('vr' not in factors):
                            data = data.drop('volume_ratio', axis=1)
                        if ('vr' in factors) and ('tor' not in factors):
                            data = data.drop('turnover_rate', axis=1)
                elif freq == 'W':
                    data = await api.weekly_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif freq == 'M':
                    data = await api.monthly_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.stk_mins_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)
                    data['trade_date'] = data['trade_time'].map(lambda x: x.replace('-', '')[0:8])
                    data['pre_close'] = data['close'].shift(-1)

                if adj is not None:
                    fcts = await api.adj_factor_vip(ts_code=ts_code, start_date=start_date, end_date=end_date)
                    fcts = fcts[['trade_date', 'adj_factor']]
                    if fcts.shape[0] == 0:
                        return None
                    data = data.set_index('trade_date', drop=False).merge(fcts.set_index('trade_date'), left_index=True, right_index=True, how='left')
                    if 'min' in freq:
                        data = data.sort_values('trade_time', ascending=False)
                    data['adj_factor'] = data['adj_factor'].fillna(method='bfill')
                    for col in PRICE_COLS:
                        if adj == 'hfq':
                            data[col] = data[col] * data['adj_factor']
                        if adj == 'qfq':
                            data[col] = data[col] * data['adj_factor'] / float(fcts['adj_factor'].iloc[0])
                        data[col] = data[col].map(FORMAT)
                        data[col] = data[col].astype(float)
                    if adjfactor is False:
                        data = data.drop('adj_factor', axis=1)
                    if 'min' not in freq:
                        data['change'] = data['close'] - data['pre_close']
                        data['pct_chg'] = data['change'] / data['pre_close'] * 100
                        data['pct_chg'] = data['pct_chg'].map(lambda x: FORMAT(x)).astype(float)
                    else:
                        data = data.drop(['trade_date', 'pre_close'], axis=1)
                else:
                    data['pre_close'] = data['close'].shift(-1)
                    data['change'] = data['close'] - data['pre_close']
                    data['pct_chg'] = data['change'] / data['pre_close'] * 100
                    data['pct_chg'] = data['pct_chg'].map(lambda x: FORMAT(x)).astype(float)

            elif asset == 'I':
                if freq == 'D':
                    data = await api.index_daily_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif freq == 'W':
                    data = await api.index_weekly_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif freq == 'M':
                    data = await api.index_monthly_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.stk_mins_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)

            elif asset == 'FT':
                if freq == 'D':
                    data = await api.fut_daily_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, exchange=exchange, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.ft_mins_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)

            elif asset == 'O':
                if freq == 'D':
                    data = await api.opt_daily_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, exchange=exchange, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.opt_mins_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)

            elif asset == 'CB':
                if freq == 'D':
                    data = await api.cb_daily_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)

            elif asset == 'FD':
                if freq == 'D':
                    data = await api.fund_daily_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, offset=offset, limit=limit)
                elif 'min' in freq:
                    data = await api.stk_mins_vip(ts_code=ts_code, start_date=start_date, end_date=end_date, freq=freq, offset=offset, limit=limit)

            elif asset == 'C':
                if freq == 'd':
                    freq = 'daily'
                elif freq == 'w':
                    freq = 'week'
                data = await api.coinbar(exchange=exchange, symbol=ts_code, freq=freq, start_date=start_date, end_date=end_date,
                                       contract_type=contract_type)

            # 计算均线
            if data is not None and ma is not None and len(ma) > 0:
                for a in ma:
                    if isinstance(a, int):
                        data['ma%s' % a] = MA(data['close'], a).map(FORMAT).shift(-(a-1))
                        data['ma%s' % a] = data['ma%s' % a].astype(float)
                        data['ma_v_%s' % a] = MA(data['vol'], a).map(FORMAT).shift(-(a-1))
                        data['ma_v_%s' % a] = data['ma_v_%s' % a].astype(float)

            if data is not None:
                data = data.reset_index(drop=True)

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)  # 异步等待重试
        else:
            if data is not None:
                if fields is not None and fields != '':
                    f_list = [col.strip() for col in fields.split(',')]
                    data = data[f_list]
                return data

    raise IOError('ERROR: All retry attempts failed.')


async def async_subs(token=''):
    """
    异步订阅功能（注意：订阅功能可能不需要异步化，因为它们通常是长连接）
    """
    if token == '' or token is None:
        token = upass.get_token()

    # 这里保持原有的同步实现，因为订阅通常是长连接
    from tushare.subs.ts_subs.subscribe import TsSubscribe
    app = TsSubscribe(token=token)
    return app


async def async_ht_subs(username, password):
    """
    异步华泰订阅功能（注意：订阅功能可能不需要异步化，因为它们通常是长连接）
    """
    # 这里保持原有的同步实现，因为订阅通常是长连接
    from tushare.subs.ht_subs.subscribe import InsightSubscribe
    app = InsightSubscribe(username, password)
    return app


# 批量数据获取功能
async def async_batch_pro_bar(ts_codes_list, **kwargs):
    """
    批量异步获取多只股票的BAR数据
    
    Parameters
    ----------
    ts_codes_list : list
        股票代码列表
    **kwargs
        其他pro_bar参数
        
    Returns
    -------
    dict
        以股票代码为key，DataFrame为value的字典
    """
    tasks = []
    for ts_code in ts_codes_list:
        task = async_pro_bar(ts_code=ts_code, **kwargs)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 构建结果字典
    result_dict = {}
    for i, ts_code in enumerate(ts_codes_list):
        if not isinstance(results[i], Exception):
            result_dict[ts_code] = results[i]
        else:
            print(f"获取 {ts_code} 数据失败: {results[i]}")
            result_dict[ts_code] = None
    
    return result_dict


async def async_multi_asset_data(requests_list):
    """
    异步获取多种资产类型的数据
    
    Parameters
    ----------
    requests_list : list
        请求列表，每个元素是一个包含参数的字典
        例如: [
            {'ts_code': '000001.SZ', 'asset': 'E'},
            {'ts_code': '000016.SH', 'asset': 'I'},
            {'ts_code': 'rb2301.SHF', 'asset': 'FT'}
        ]
        
    Returns
    -------
    list
        结果列表，与请求列表对应
    """
    tasks = []
    for request in requests_list:
        task = async_pro_bar(**request)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results


# 使用示例
async def example_usage():
    """异步使用示例"""
    print("=== 异步 data_pro 使用示例 ===")
    
    # 1. 异步获取单只股票数据
    print("1. 获取单只股票日线数据...")
    try:
        data = await async_pro_bar(ts_code='000001.SZ', start_date='20231201', end_date='20231231')
        if data is not None:
            print(f"   ✅ 获取到 {len(data)} 条数据")
            print(data.head())
        else:
            print("   ⚠️ 返回数据为空")
    except Exception as e:
        print(f"   ❌ 获取失败: {e}")
    
    # 2. 批量获取多只股票数据
    print("\n2. 批量获取多只股票数据...")
    try:
        ts_codes = ['000001.SZ', '000002.SZ', '600000.SH']
        batch_data = await async_batch_pro_bar(ts_codes, start_date='20231201', end_date='20231231')
        
        success_count = sum(1 for v in batch_data.values() if v is not None)
        print(f"   ✅ 批量获取完成: {success_count}/{len(ts_codes)} 成功")
        
        for code, df in batch_data.items():
            if df is not None:
                print(f"   {code}: {len(df)} 条数据")
            else:
                print(f"   {code}: 获取失败")
                
    except Exception as e:
        print(f"   ❌ 批量获取失败: {e}")
    
    # 3. 多种资产类型数据
    print("\n3. 获取多种资产类型数据...")
    try:
        requests = [
            {'ts_code': '000001.SZ', 'asset': 'E', 'start_date': '20231201', 'end_date': '20231231'},  # 股票
            {'ts_code': '000016.SH', 'asset': 'I', 'start_date': '20231201', 'end_date': '20231231'},  # 指数
        ]
        
        multi_results = await async_multi_asset_data(requests)
        
        success_count = sum(1 for r in multi_results if not isinstance(r, Exception))
        print(f"   ✅ 多资产获取完成: {success_count}/{len(requests)} 成功")
        
    except Exception as e:
        print(f"   ❌ 多资产获取失败: {e}")


if __name__ == '__main__':
    # 运行示例
    asyncio.run(example_usage())
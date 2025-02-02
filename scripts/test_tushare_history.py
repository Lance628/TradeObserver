import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

def test_get_hist_data():
    """测试get_hist_data接口"""
    print("\n=== 测试 get_hist_data ===")
    try:
        # 测试日K线
        df_daily = ts.get_hist_data('600000', start='2025-01-01', end='2025-01-10')
        print("日K线数据示例:")
        print(df_daily.head() if df_daily is not None else "未获取到数据")
        
        # 测试分钟K线
        df_min = ts.get_hist_data('600000', start='2025-01-10', ktype='5')
        print("\n5分钟K线数据示例:")
        print(df_min.head() if df_min is not None else "未获取到数据")
        
    except Exception as e:
        print(f"get_hist_data测试出错: {str(e)}")

def test_get_k_data():
    """测试get_k_data接口"""
    print("\n=== 测试 get_k_data ===")
    try:
        # 测试日K线
        df_daily = ts.get_k_data('600000', start='2025-01-01', end='2025-01-10')
        print("日K线数据示例:")
        print(df_daily.head() if df_daily is not None else "未获取到数据")
        
        # 测试分钟K线
        df_min = ts.get_k_data('600000', ktype='5')
        print("\n5分钟K线数据示例:")
        print(df_min.head() if df_min is not None else "未获取到数据")
        
    except Exception as e:
        print(f"get_k_data测试出错: {str(e)}")

def test_bar():
    """测试bar接口"""
    print("\n=== 测试 bar ===")
    try:
        # 获取API连接
        cons = ts.get_apis()
        
        # 测试日K线
        df_daily = ts.bar('600000', conn=cons, start_date='2025-01-01', end_date='2025-01-10')
        print("日K线数据示例:")
        print(df_daily.head() if df_daily is not None else "未获取到数据")
        
        # 测试分钟K线
        df_min = ts.bar('600000', conn=cons, freq='5min')
        print("\n5分钟K线数据示例:")
        print(df_min.head() if df_min is not None else "未获取到数据")
        
        # 关闭连接
        ts.close_apis(cons)
        
    except Exception as e:
        print(f"bar测试出错: {str(e)}")

def main():
    """主函数"""
    print("开始测试tushare历史数据接口...")
    
    test_get_hist_data()
    test_get_k_data()
    test_bar()
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 
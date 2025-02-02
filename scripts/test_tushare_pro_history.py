import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

# 设置token（请替换为您的token）
ts.set_token('e8537fb5ca8b4f700997e34289d7406f8481977a86a2af2df26d3b30')
pro = ts.pro_api()

def test_daily_data():
    """测试日线数据获取"""
    print("\n=== 测试日线数据 ===")
    try:
        # 获取日线数据
        df_daily = pro.daily(ts_code='588200.SH', 
                           start_date='20250101', 
                           end_date='20250110')
        print("日线数据示例:")
        print(df_daily.head() if not df_daily.empty else "未获取到数据")
        
        # 获取日线基础信息
        df_daily_basic = pro.daily_basic(ts_code='588200.SH',
                                       start_date='20250101',
                                       end_date='20250110')
        print("\n日线基础信息示例:")
        print(df_daily_basic.head() if not df_daily_basic.empty else "未获取到数据")
        
    except Exception as e:
        print(f"日线数据测试出错: {str(e)}")

def test_min_data():
    """测试分钟线数据获取"""
    print("\n=== 测试分钟线数据 ===")
    try:
        # 注意：分钟级别数据需要积分或者付费权限
        df_min = pro.stk_mins(ts_code='588200.SH',
                             start_date='20250110 09:30:00',
                             end_date='20250110 15:00:00',
                             freq='5min')
        print("5分钟线数据示例:")
        print(df_min)
        print(df_min.head() if not df_min.empty else "未获取到数据")
        
    except Exception as e:
        print(f"分钟线数据测试出错: {str(e)}")

def test_adj_factor():
    """测试复权因子获取"""
    print("\n=== 测试复权因子 ===")
    try:
        df_adj = pro.adj_factor(ts_code='588200.SH',
                               start_date='20250101',
                               end_date='20250110')
        print("复权因子数据示例:")
        print(df_adj.head() if not df_adj.empty else "未获取到数据")
        
    except Exception as e:
        print(f"复权因子测试出错: {str(e)}")

def main():
    """主函数"""
    print("开始测试tushare pro历史数据接口...")
    
    test_daily_data()
    test_min_data()
    test_adj_factor()
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 
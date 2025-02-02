import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

# 设置token
ts.set_token('e8537fb5ca8b4f700997e34289d7406f8481977a86a2af2df26d3b30')

def test_pro_bar():
    """测试pro_bar接口获取K线数据"""
    print("\n=== 测试 pro_bar 接口 ===")
    try:
        # 获取日K线数据
        df_daily = ts.pro_bar(
            ts_code='588200.SH',
            start_date='20250101',
            end_date='20250110',
            freq='D',
            asset='E',
            adj='qfq'  # qfq-前复权 hfq-后复权 None-不复权
        )
        print("\n日K线数据示例:")
        print(df_daily.head() if not df_daily.empty else "未获取到数据")
        
        # 获取分钟级别数据
        df_min = ts.pro_bar(
            ts_code='588200.SH',
            start_date='20250110 09:30:00',
            end_date='20250110 15:00:00',
            freq='1min',  # 支持1min/5min/15min/30min/60min
            asset='E',
            adj='qfq'
        )
        print("\n分钟线数据示例:")
        print(df_min.head() if not df_min.empty else "未获取到数据")
        
        # 获取周K线数据
        df_weekly = ts.pro_bar(
            ts_code='588200.SH',
            start_date='20250101',
            end_date='20250110',
            freq='W',  # W-周 M-月
            asset='E',
            adj='qfq'
        )
        print("\n周K线数据示例:")
        print(df_weekly.head() if not df_weekly.empty else "未获取到数据")

    except Exception as e:
        print(f"pro_bar测试出错: {str(e)}")

def main():
    """主函数"""
    print("开始测试tushare pro_bar接口...")
    test_pro_bar()
    print("\n测试完成!")

if __name__ == "__main__":
    main() 
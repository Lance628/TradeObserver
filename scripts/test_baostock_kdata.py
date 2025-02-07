import baostock as bs
import pandas as pd
from datetime import datetime

def test_query_history_k_data():
    """测试 baostock 的历史K线数据查询功能"""
    
    # 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f'登录失败: {lg.error_msg}')
        return
    
    try:
        # 获取沪深300指数的日K线数据
        code = "sh.588200"  # 沪深300指数
        start_date = '2024-01-01'
        end_date = '2024-03-15'
        
        rs = bs.query_history_k_data_plus(
            code,
            "date,code,open,high,low,close,volume,amount",
            start_date=start_date,
            end_date=end_date,
            frequency="d",  # 日线数据
            adjustflag="3"  # 不复权
        )
        
        if rs.error_code != '0':
            print(f'查询失败: {rs.error_msg}')
            return
            
        # 将数据转换为DataFrame
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 打印数据基本信息
        print("\n数据概览:")
        print(f"数据时间范围: {start_date} 至 {end_date}")
        print(f"获取到的数据条数: {len(df)}")
        print("\n前5条数据:")
        print(df.head())
        
        # 数据完整性检查
        print("\n数据完整性检查:")
        print(f"是否存在空值: {df.isnull().any().any()}")
        
        # 保存数据到CSV文件
        filename = f"baostock_sh588200_{start_date}_{end_date}.csv"
        df.to_csv(filename, index=False)
        print(f"\n数据已保存至: {filename}")
        
    finally:
        # 退出系统
        bs.logout()

def test_query_minute_k_data():
    """测试 baostock 的分钟级K线数据查询功能"""
    
    # 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f'登录失败: {lg.error_msg}')
        return
    
    try:
        # 获取沪深300指数的5分钟K线数据
        code = "sh.588200"
        start_date = '2024-03-14'  # 由于分钟数据量较大，这里只查询最近几天的数据
        end_date = '2024-03-15'
        
        rs = bs.query_history_k_data_plus(
            code,
            "date,time,code,open,high,low,close,volume,amount",
            start_date=start_date,
            end_date=end_date,
            frequency="5",  # 5分钟线
            adjustflag="3"  # 不复权
        )
        
        if rs.error_code != '0':
            print(f'查询失败: {rs.error_msg}')
            return
            
        # 将数据转换为DataFrame
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 打印数据基本信息
        print("\n5分钟K线数据概览:")
        print(f"数据时间范围: {start_date} 至 {end_date}")
        print(f"获取到的数据条数: {len(df)}")
        print("\n前5条数据:")
        print(df.head())
        
        # 数据完整性检查
        print("\n数据完整性检查:")
        print(f"是否存在空值: {df.isnull().any().any()}")
        
        # 保存数据到CSV文件
        filename = f"baostock_sh588200_5min_{start_date}_{end_date}.csv"
        df.to_csv(filename, index=False)
        print(f"\n数据已保存至: {filename}")
        
    finally:
        # 退出系统
        bs.logout()

if __name__ == "__main__":
    print("测试日K线数据查询:")
    test_query_history_k_data()
    print("\n" + "="*50 + "\n")
    print("测试5分钟K线数据查询:")
    test_query_minute_k_data() 
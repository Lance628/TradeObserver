import sys
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
sys.path.append('..')  
from src.utils.time_utils import is_trading_day

def generate_time_series(start_date, end_date, freq):
    """生成时间序列"""
    # 将字符串转换为datetime对象
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    if freq == '1d':
        # 生成所有日期
        all_dates = pd.date_range(start=start, end=end, freq='D')
        # 过滤出交易日
        trading_dates = [d for d in all_dates if is_trading_day(d)]
        # 设置交易时间为15:00
        dates = [d.replace(hour=15, minute=0) for d in trading_dates]
        return pd.DatetimeIndex(dates)
    
    elif freq in ['1min', '5min', '15min', '30min', '60min', '120min']:
        times = []
        minutes = int(freq.replace('min', ''))
        
        # 遍历每一天
        current_date = start
        while current_date <= end:
            # 只处理交易日
            if is_trading_day(current_date):
                # 上午时段
                morning_start = current_date.replace(hour=9, minute=30)
                morning_end = current_date.replace(hour=11, minute=30)
                # 下午时段
                afternoon_start = current_date.replace(hour=13, minute=0)
                afternoon_end = current_date.replace(hour=15, minute=0)
                
                # 生成上午时段
                current = morning_start
                while current <= morning_end:
                    times.append(current)
                    current += timedelta(minutes=minutes)
                
                # 生成下午时段
                current = afternoon_start
                while current <= afternoon_end:
                    times.append(current)
                    current += timedelta(minutes=minutes)
            
            current_date += timedelta(days=1)
                
        return pd.DatetimeIndex(times)
    
    return pd.DatetimeIndex([])

def create_kline_template(start_date, end_date, output_file):
    """创建K线模板Excel文件"""
    # 定义所有周期
    frequencies = ['1min', '5min', '15min', '30min', '60min', '120min', '1d']
    
    # 创建Excel writer对象
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        print(output_file)
        # 为每个周期创建一个sheet
        for freq in frequencies:
            # 生成时间序列
            times = generate_time_series(start_date, end_date, freq)
            
            # 创建DataFrame
            df = pd.DataFrame(index=times)
            df['datetime'] = times
            df['open'] = np.nan
            df['high'] = np.nan
            df['low'] = np.nan
            df['close'] = np.nan
            
            # 设置datetime列格式
            df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 写入Excel，设置sheet名
            sheet_name = freq.replace('min', 'min_kline').replace('1d', 'daily_kline')
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 获取worksheet
            worksheet = writer.sheets[sheet_name]
            
            # 调整列宽
            worksheet.column_dimensions['A'].width = 20  # datetime列
            worksheet.column_dimensions['B'].width = 12  # open列
            worksheet.column_dimensions['C'].width = 12  # high列
            worksheet.column_dimensions['D'].width = 12  # low列
            worksheet.column_dimensions['E'].width = 12  # close列
            
            print(f"{sheet_name}: 生成了 {len(times)} 条时间记录")

def main():
    # 设置开始和结束日期
    start_date = '2024-01-01'
    end_date = '2024-01-10'
    output_file = 'kline_template.xlsx'
    
    print(f"开始创建K线模板，时间范围：{start_date} 到 {end_date}")
    create_kline_template(start_date, end_date, output_file)
    print(f"模板创建完成，文件保存为：{output_file}")

if __name__ == "__main__":
    main() 
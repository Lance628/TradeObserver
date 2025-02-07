import pandas as pd
import sqlite3
from datetime import datetime
import argparse
import os

def parse_header(first_line):
    """解析CSV文件第一行，获取code和period"""
    parts = first_line.strip().split(' ')
    code = parts[0]
    period = 1  # 默认为1分钟
    for part in parts:
        if '分钟线' in part:
            period = int(part.replace('分钟线', ''))
    return code, period

def combine_datetime(date_str, time_str):
    """将日期和时间字符串组合成datetime对象"""
    date = datetime.strptime(date_str, '%Y/%m/%d')
    # 处理4位数的时间字符串
    time_str = f"{int(time_str):04d}"
    hour = int(time_str[:2])
    minute = int(time_str[2:])
    return date.replace(hour=hour, minute=minute, second=0)

def is_trading_time(timestamp):
    """判断是否为交易时间"""
    hour = timestamp.hour
    minute = timestamp.minute
    if hour == 9 and minute >= 30:
        return True
    if hour == 11 and minute <= 30:
        return True
    if hour == 10:
        return True
    if hour >= 13 and hour < 15:
        return True
    if hour == 15 and minute == 0:
        return True
    return False

def aggregate_to_higher_timeframe(df, period):
    """将较低时间周期数据聚合成较高时间周期"""
    # 确保timestamp是datetime类型
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 过滤出交易时间的数据
    df['is_trading'] = df['timestamp'].apply(is_trading_time)
    df = df[df['is_trading']].copy()
    
    # 按天分组处理
    grouped = df.groupby(df['timestamp'].dt.date)
    result_dfs = []
    
    for date, group in grouped:
        if period == 60:
            # 60分钟级别：9:30-10:30, 10:30-11:30, 13:00-14:00, 14:00-15:00
            time_ranges = [
                ('09:30:00', '10:30:00'),
                ('10:30:00', '11:30:00'),
                ('13:00:00', '14:00:00'),
                ('14:00:00', '15:00:00')
            ]
            
            for start_time, end_time in time_ranges:
                mask = (group['timestamp'].dt.strftime('%H:%M:%S') > start_time) & \
                       (group['timestamp'].dt.strftime('%H:%M:%S') <= end_time)
                period_data = group[mask]
                
                if not period_data.empty:
                    aggregated = pd.DataFrame({
                        'timestamp': [period_data['timestamp'].max()],
                        '开盘': [period_data['开盘'].iloc[0]],
                        '最高': [period_data['最高'].max()],
                        '最低': [period_data['最低'].min()],
                        '收盘': [period_data['收盘'].iloc[-1]],
                        '成交量': [period_data['成交量'].sum()],
                        '成交额': [period_data['成交额'].sum()]
                    })
                    result_dfs.append(aggregated)
                    
        elif period == 120:
            # 120分钟级别：9:30-11:30, 13:00-15:00
            time_ranges = [
                ('09:30:00', '11:30:00'),
                ('13:00:00', '15:00:00')
            ]
            
            for start_time, end_time in time_ranges:
                mask = (group['timestamp'].dt.strftime('%H:%M:%S') > start_time) & \
                       (group['timestamp'].dt.strftime('%H:%M:%S') <= end_time)
                period_data = group[mask]
                
                if not period_data.empty:
                    aggregated = pd.DataFrame({
                        'timestamp': [period_data['timestamp'].max()],
                        '开盘': [period_data['开盘'].iloc[0]],
                        '最高': [period_data['最高'].max()],
                        '最低': [period_data['最低'].min()],
                        '收盘': [period_data['收盘'].iloc[-1]],
                        '成交量': [period_data['成交量'].sum()],
                        '成交额': [period_data['成交额'].sum()]
                    })
                    result_dfs.append(aggregated)
                    
        elif period == 240:
            # 240分钟级别：按天聚合
            if not group.empty:
                aggregated = pd.DataFrame({
                    'timestamp': [group['timestamp'].max()],
                    '开盘': [group['开盘'].iloc[0]],
                    '最高': [group['最高'].max()],
                    '最低': [group['最低'].min()],
                    '收盘': [group['收盘'].iloc[-1]],
                    '成交量': [group['成交量'].sum()],
                    '成交额': [group['成交额'].sum()]
                })
                result_dfs.append(aggregated)
        else:
            # 其他周期（如15、30分钟）使用常规重采样
            resampled = group.resample(
                f'{period}T', 
                on='timestamp',
                closed='right',
                label='right'
            ).agg({
                '开盘': 'first',
                '最高': 'max',
                '最低': 'min',
                '收盘': 'last',
                '成交量': 'sum',
                '成交额': 'sum'
            }).dropna()
            
            resampled = resampled.reset_index()
            resampled = resampled[resampled['timestamp'].apply(is_trading_time)]
            result_dfs.append(resampled)
    
    # 合并所有结果
    if result_dfs:
        final_df = pd.concat(result_dfs, ignore_index=True)
        return final_df.sort_values('timestamp')
    return pd.DataFrame()

def update_database(db_path, csv_path, clear_table=False):
    """更新数据库中的candles表"""
    # 尝试不同的编码方式读取文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
    first_line = None
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                first_line = f.readline()
                code, base_period = parse_header(first_line)
                
                # 跳过前两行，从第三行开始读取数据
                df = pd.read_csv(csv_path, skiprows=2, header=None, encoding=encoding)
                break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"使用 {encoding} 编码读取文件时发生错误: {str(e)}")
            continue
    
    if first_line is None:
        raise Exception("无法正确读取文件，请检查文件编码")

    df.columns = ["日期", "时间", "开盘", "最高", "最低", "收盘", "成交量", "成交额"]
    
    # 删除包含空值的行
    df = df.dropna()
    
    # 转换timestamp
    df['timestamp'] = df.apply(lambda x: combine_datetime(x['日期'], x['时间']), axis=1)
    
    # 准备数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 如果需要，清空表
    if clear_table:
        cursor.execute("DELETE FROM candles")
        print("已清空candles表")
    
    # 如果是5分钟数据，需要同时更新多个周期
    periods_to_update = [base_period]
    if base_period == 5:
        periods_to_update.extend([15, 30, 60, 120, 240])
    
    try:
        for period in periods_to_update:
            if period == base_period:
                current_df = df
            else:
                # 对于更高级别的周期，需要先进行聚合
                current_df = aggregate_to_higher_timeframe(df, period)
            current_df.to_csv(f"data/etf_prices_{code}_{period}.csv", index=True)
            # 逐行更新数据库
            for _, row in current_df.iterrows():
                timestamp = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                # 检查记录是否存在
                cursor.execute("""
                    SELECT COUNT(*) FROM candles 
                    WHERE timestamp = ? AND code = ? AND period = ?
                """, (timestamp, code, period))
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # 更新现有记录
                    cursor.execute("""
                        UPDATE candles 
                        SET open = ?, high = ?, low = ?, close = ?, volume = ?, amount = ?
                        WHERE timestamp = ? AND code = ? AND period = ?
                    """, (
                        float(row['开盘']), float(row['最高']), float(row['最低']), 
                        float(row['收盘']), float(row['成交量']), float(row['成交额']),
                        timestamp, code, period
                    ))
                else:
                    # 插入新记录
                    cursor.execute("""
                        INSERT INTO candles (timestamp, code, period, open, high, low, close, volume, amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp, code, period,
                        float(row['开盘']), float(row['最高']), float(row['最低']), 
                        float(row['收盘']), float(row['成交量']), float(row['成交额'])
                    ))
            
            print(f"已更新 {code} 的 {period} 分钟数据")
        
        conn.commit()
        print("数据库更新完成")
        
    except Exception as e:
        print(f"更新过程中出现错误: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='更新ETF价格数据库')
    parser.add_argument('csv_path', help='CSV文件路径')
    parser.add_argument('--clear', action='store_true', help='是否清空现有数据')
    parser.add_argument('--db_path', default='data/etf_prices.db', help='数据库文件路径')
    
    args = parser.parse_args()
    
    update_database(args.db_path, args.csv_path, args.clear) 
import tushare as ts
import sqlite3
import time
from datetime import datetime

# 初始化 Tushare
# 请替换为你的 token
ts.set_token('e8537fb5ca8b4f700997e34289d7406f8481977a86a2af2df26d3b30')
pro = ts.pro_api()

# 创建数据库连接
def create_database():
    conn = sqlite3.connect('etf_prices.db')
    cursor = conn.cursor()
    
    # 创建表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etf_prices (
            timestamp DATETIME,
            code VARCHAR(10),
            price FLOAT,
            volume FLOAT,
            amount FLOAT
        )
    ''')
    conn.commit()
    return conn

def get_realtime_price(code):
    try:
        df = ts.get_realtime_quotes(code)
        if df is not None and not df.empty:
            return {
                'price': float(df['price'][0]),
                'volume': float(df['volume'][0]),
                'amount': float(df['amount'][0])
            }
    except Exception as e:
        print(f"获取{code}数据时出错: {str(e)}")
    return None

def main():
    conn = create_database()
    cursor = conn.cursor()
    
    # 监控的ETF代码列表
    etf_codes = ['588200', '510300']
    
    try:
        while True:
            current_time = datetime.now()
            
            # 判断是否在交易时间内（9:30-11:30, 13:00-15:00）
            hour = current_time.hour
            minute = current_time.minute
            # if not ((hour == 9 and minute >= 30) or 
            #         (hour == 10) or 
            #         (hour == 11 and minute <= 30) or
            #         (hour >= 13 and hour < 15)):
            #     print("当前不是交易时间，等待中...")
            #     time.sleep(60)
            #     continue
                
            for code in etf_codes:
                data = get_realtime_price(code)
                if data:
                    cursor.execute('''
                        INSERT INTO etf_prices (timestamp, code, price, volume, amount)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (current_time, code, data['price'], data['volume'], data['amount']))
                    conn.commit()
                    print(f"{current_time} - {code}: 价格={data['price']}, 成交量={data['volume']}")
            
            time.sleep(3)  # 每3秒更新一次
            
    except KeyboardInterrupt:
        print("\n程序已停止")
        conn.close()

if __name__ == "__main__":
    main()

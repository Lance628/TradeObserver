import pandas as pd
import sqlite3
from datetime import datetime

def create_tables(conn):
    """创建数据表（如果不存在）"""
    cursor = conn.cursor()
    
    # 创建各个周期的表
    periods = ['1min', '5min', '15min', '30min', '60min', 'daily']
    for period in periods:
        table_name = f'kline_{period}'
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            datetime TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    
    conn.commit()

def import_kline_data(excel_file, db_file):
    """从Excel导入K线数据到数据库"""
    # 连接数据库
    conn = sqlite3.connect(db_file)
    create_tables(conn)
    
    # 读取Excel的所有sheet
    xls = pd.ExcelFile(excel_file)
    sheet_names = xls.sheet_names
    
    total_rows = 0
    imported_rows = 0
    
    for sheet_name in sheet_names:
        # 读取sheet数据
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # 确定对应的数据库表名
        table_name = sheet_name.replace('_kline', '')
        db_table = f'kline_{table_name}'
        
        total_rows += len(df)
        
        # 过滤掉任意一个价格为空的行
        df_filtered = df.dropna(subset=['open', 'high', 'low', 'close'])
        imported_rows += len(df_filtered)
        
        # 如果没有有效数据，继续下一个sheet
        if len(df_filtered) == 0:
            continue
        
        # 添加创建时间
        df_filtered['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 写入数据库
        df_filtered.to_sql(db_table, conn, if_exists='append', index=False)
        
        print(f"表 {db_table} 导入了 {len(df_filtered)} 行数据")
    
    print(f"\n总行数: {total_rows}")
    print(f"成功导入: {imported_rows}")
    print(f"跳过行数: {total_rows - imported_rows}")
    
    conn.close()

def main():
    excel_file = 'kline_template.xlsx'
    db_file = 'data/etf_prices.db'
    
    print(f"开始从 {excel_file} 导入数据到 {db_file}")
    import_kline_data(excel_file, db_file)
    print("导入完成!")

if __name__ == "__main__":
    main() 
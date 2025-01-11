import sqlite3
from ..config.settings import DATABASE_PATH
from ..utils.logger import setup_logger
from ..models.candle import Candle
from typing import List
from datetime import datetime

logger = setup_logger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """初始化数据库和所有必要的表"""
        # 确保数据库目录存在
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建实时价格表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etf_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    code VARCHAR(10) NOT NULL,
                    price FLOAT NOT NULL,
                    volume FLOAT NOT NULL,
                    amount FLOAT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建K线数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candles (
                    timestamp DATETIME NOT NULL,
                    code TEXT NOT NULL,
                    period INTEGER NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    amount REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (timestamp, code, period)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_etf_prices_code_time 
                ON etf_prices (code, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_candles_code_period_time 
                ON candles (code, period, timestamp)
            ''')
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def save_price_data(self, timestamp, code, price_data):
        """保存价格数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO etf_prices (timestamp, code, price, volume, amount)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    code,
                    price_data['price'],
                    price_data['volume'],
                    price_data['amount']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存数据时出错: {str(e)}")
            raise

    def save_candle(self, candle: Candle):
        """保存K线数据到数据库"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO candles (
                    timestamp, code, period, open, high, low, close, 
                    volume, amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                candle.timestamp, candle.code, candle.period,
                candle.open, candle.high, candle.low, candle.close,
                candle.volume, candle.amount
            ))
            conn.commit()

    def get_candles(self, code: str, period: int, limit: int) -> List[Candle]:
        """从数据库获取历史K线数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, code, period, open, high, low, close, volume, amount 
                FROM candles 
                WHERE code = ? AND period = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (code, period, limit))
            
            rows = cursor.fetchall()
            return [
                Candle(
                    timestamp=row[0],  # 使用索引位置访问
                    code=row[1],
                    period=row[2],
                    open=row[3],
                    high=row[4],
                    low=row[5],
                    close=row[6],
                    volume=row[7],
                    amount=row[8]
                )
                for row in reversed(rows)
            ]

    def get_price_data(self, code: str, start_date: datetime, end_date: datetime) -> List[tuple]:
        """获取指定时间范围内的价格数据
        
        Args:
            code: ETF代码
            start_date: 开始时间
            end_date: 结束时间
            
        Returns:
            List[tuple]: 价格数据列表，每个元素为 (code, timestamp, price, volume, amount)
        """
        try:
            query = """
                SELECT code, timestamp, price, volume, amount 
                FROM etf_prices 
                WHERE code = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """
            
            # 确保日期格式正确
            start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            with self.get_connection() as conn:
                # 设置 row_factory 以便正确处理日期时间
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (code, start_str, end_str))
                rows = cursor.fetchall()
                
                # 将结果转换为适当的格式
                return [(
                    row['code'],
                    datetime.strptime(row['timestamp'].split('.')[0], '%Y-%m-%d %H:%M:%S'),
                    row['price'],
                    row['volume'],
                    row['amount']
                ) for row in rows]
                
        except Exception as e:
            logger.error(f"获取价格数据失败: {str(e)}")
            return []

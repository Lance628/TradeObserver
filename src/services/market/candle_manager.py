from datetime import datetime
import time
from typing import Dict, List, Optional
from collections import defaultdict
import threading
from queue import Queue
from ...models.candle import Candle
from ...database.database import DatabaseManager
from ...utils.logger import setup_logger
from ...config.settings import CANDLE_PERIODS

class CandleManager(threading.Thread):
    def __init__(self):
        super().__init__()
        self.periods = CANDLE_PERIODS
        self.logger = setup_logger(__name__)
        self.db_manager = DatabaseManager()
        self._candles = defaultdict(lambda: {})
        self._price_queue = Queue()
        self._running = True

    def run(self):
        """线程主循环"""
        self.logger.info("K线管理器启动")
        while self._running:
            try:
                # 从队列中获取价格数据
                price_data = self._price_queue.get()
                if price_data is None:  # 停止信号
                    time.sleep(1)
                    continue
                    
                code, timestamp, price, volume, amount = price_data
                for period in self.periods:
                    self._update_candle(code, period, timestamp, price, volume, amount)
                    
            except Exception as e:
                self.logger.error(f"处理K线数据错误: {str(e)}")
                
        self.logger.info("K线管理器已停止")

    def stop(self):
        """停止线程"""
        self._running = False
        self._price_queue.put(None)  # 发送停止信号

    def on_price_update(self, code: str, timestamp: datetime, 
                       price: float, volume: float, amount: float):
        """处理实时价格更新"""
        self._price_queue.put((code, timestamp, price, volume, amount))

    def _get_period_start_time(self, timestamp: datetime, period: int) -> datetime:
        """计算K线周期的开始时间
        
        Args:
            timestamp: 当前时间戳
            period: K线周期（分钟）
            
        Returns:
            datetime: 当前K线的开始时间
        """
        # 将分钟数转换为总分钟数
        total_minutes = timestamp.hour * 60 + timestamp.minute
        # 计算当前周期的开始分钟数
        period_start_minutes = (total_minutes // period) * period
        # 构建新的datetime对象
        return timestamp.replace(
            hour=period_start_minutes // 60,
            minute=period_start_minutes % 60,
            second=0,
            microsecond=0
        )

    def _update_candle(self, code: str, period: int, timestamp: datetime, 
                      price: float, volume: float, amount: float):
        """更新指定周期的K线"""
        period_start = self._get_period_start_time(timestamp, period)
        candle_key = (code, period)
        
        if candle_key not in self._candles or \
           self._candles[candle_key].timestamp != period_start:
            # 保存旧的K线
            if candle_key in self._candles:
                self._save_candle(self._candles[candle_key])
            
            # 创建新的K线
            self._candles[candle_key] = Candle(
                timestamp=period_start,
                code=code,
                period=period,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume,
                amount=amount
            )
        else:
            # 更新现有K线
            current_candle = self._candles[candle_key]
            current_candle.high = max(current_candle.high, price)
            current_candle.low = min(current_candle.low, price)
            current_candle.close = price
            current_candle.volume += volume
            current_candle.amount += amount
    
    def _save_candle(self, candle: Candle):
        """保存K线到数据库"""
        try:
            self.db_manager.save_candle(candle)
            self.logger.debug(f"K线已保存: {candle.code} {candle.period}分钟 {candle.timestamp}")
        except Exception as e:
            self.logger.error(f"保存K线失败: {str(e)}")

    def save_and_clear_current_candles(self, code: str = None):
        """保存并清理当前所有K线数据
        
        Args:
            code: ETF代码，如果为None则处理所有代码的K线
        """
        try:
            # 获取需要处理的candle_keys
            candle_keys = []
            if code:
                # 只处理指定code的所有周期
                candle_keys = [(code, period) for period in self.periods]
            else:
                # 处理所有已存在的candle_keys
                candle_keys = list(self._candles.keys())
            
            # 保存并清理K线
            for candle_key in candle_keys:
                if candle_key in self._candles:
                    self._save_candle(self._candles[candle_key])
                    del self._candles[candle_key]
            
            self.logger.info(f"已保存并清理K线数据: {code if code else '所有代码'}")
            
        except Exception as e:
            self.logger.error(f"保存并清理K线数据时出错: {str(e)}")

    def check_and_save_missing_candles(self, code: str, start_date: datetime, end_date: datetime):
        """检查并保存缺失的K线数据"""
        try:
            # 从数据库获取原始价格数据
            price_data = self.db_manager.get_price_data(code, start_date, end_date)
            if not price_data:
                self.logger.info(f"未找到价格数据: {code} {start_date} - {end_date}")
                return

            # 按时间排序价格数据
            sorted_data = sorted(price_data, key=lambda x: x[1])  # x[1] 是时间戳
            
            # 处理每个价格数据点
            for data in sorted_data:
                timestamp, price, volume, amount = data[1], data[2], data[3], data[4]
                
                # 对每个周期创建K线
                for period in self.periods:
                    self._update_candle(code, period, timestamp, price, volume, amount)
            
            # 使用新方法保存并清理K线
            self.save_and_clear_current_candles(code)
            
            self.logger.info(f"完成缺失K线检查和保存: {code} {start_date} - {end_date}")
            
        except Exception as e:
            self.logger.error(f"检查缺失K线时出错: {str(e)}")
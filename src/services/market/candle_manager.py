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
from ..analyzers.realtime.hub_analyzer import HubAnalyzer

class CandleManager(threading.Thread):
    def __init__(self):
        super().__init__()
        self.periods = CANDLE_PERIODS
        self.logger = setup_logger(__name__)
        self.db_manager = DatabaseManager()
        self._candles = defaultdict(lambda: {})
        self._price_queue = Queue()
        self._running = True
        
        # 修改存储结构为 {(code, period): [analyzers]}
        self._analyzers = defaultdict(list)

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

    def _get_period_end_time(self, timestamp: datetime, period: int) -> datetime:
        """计算A股市场K线周期的结束时间
        
        Args:
            timestamp: 当前时间戳
            period: K线周期（分钟）
            
        Returns:
            datetime: 当前K线的结束时间
        """
        # 转换为当日分钟数
        hour, minute = timestamp.hour, timestamp.minute
        
        # 计算交易时间的分钟数（考虑午休时间）
        if hour < 9 or (hour == 9 and minute < 30):
            # 早于开盘时间，使用开盘时间
            total_minutes = 0
        elif hour < 11 or (hour == 11 and minute <= 30):
            # 上午交易时段
            total_minutes = (hour * 60 + minute) - (9 * 60 + 30)
        elif hour < 13:
            # 午休时间，使用上午最后一个周期
            total_minutes = 120  # 11:30 - 9:30 = 120分钟
        elif hour < 15:
            # 下午交易时段
            total_minutes = 120 + (hour * 60 + minute) - (13 * 60)
        else:
            # 收盘后，使用最后一个周期
            total_minutes = 240  # 全天交易分钟数
        
        # 计算当前周期的结束分钟数
        period_end_minutes = ((total_minutes + period) // period) * period
        
        # 将周期结束分钟数转换回实际时间
        if period_end_minutes <= 120:  # 上午时段
            actual_minutes = period_end_minutes + (9 * 60 + 30)
            return timestamp.replace(
                hour=actual_minutes // 60,
                minute=actual_minutes % 60,
                second=0,
                microsecond=0
            )
        else:  # 下午时段
            actual_minutes = (period_end_minutes - 120) + (13 * 60)
            return timestamp.replace(
                hour=actual_minutes // 60,
                minute=actual_minutes % 60,
                second=0,
                microsecond=0
            )

    def _update_candle(self, code: str, period: int, timestamp: datetime, 
                      price: float, volume: float, amount: float):
        """更新指定周期的K线"""
        period_end = self._get_period_end_time(timestamp, period)
        candle_key = (code, period)
        
        if candle_key not in self._candles or \
           self._candles[candle_key].timestamp != period_end:
            # 保存旧的K线
            if candle_key in self._candles:
                self._save_candle(self._candles[candle_key])
            
            # 创建新的K线
            self._candles[candle_key] = Candle(
                timestamp=period_end,  # 使用结束时间作为时间戳
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
        """保存K线到数据库并通知相应的分析器"""
        try:
            self.db_manager.save_candle(candle)
            self.logger.debug(f"K线已保存: {candle.code} {candle.period}分钟 {candle.timestamp}")
            
            # 通知对应code和period的所有分析器
            analyzer_key = (candle.code, candle.period)
            for analyzer in self._analyzers[analyzer_key]:
                analyzer.on_candle_update(candle.code, candle)
                
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

    def register_analyzer(self, code: str, period: int, analyzer: HubAnalyzer):
        """注册一个特定代码和周期的分析器
        
        Args:
            code: ETF代码
            period: K线周期（分钟）
            analyzer: 分析器实例
        """
        analyzer_key = (code, period)
        self._analyzers[analyzer_key].append(analyzer)
        self.logger.info(f"注册了{code} {period}分钟级别的分析器")
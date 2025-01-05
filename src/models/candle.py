from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Candle:
    """K线数据结构"""
    timestamp: datetime  # K线的起始时间
    open: float         # 开盘价
    high: float         # 最高价
    low: float          # 最低价
    close: float        # 收盘价
    volume: float       # 成交量
    amount: float       # 成交额
    code: str          # 股票代码
    period: int        # K线周期（分钟）
    
    @property
    def end_timestamp(self) -> datetime:
        """获取K线的结束时间"""
        from ..utils.time_utils import get_period_end_time
        return get_period_end_time(self.timestamp, self.period)
    
    def update(self, price: float, volume: float, amount: float):
        """更新K线数据"""
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.volume += volume
        self.amount += amount
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

class HubType(Enum):
    """中枢类型"""
    UNKNOWN = "UNKNOWN"    # 未确定
    UP = "UP"             # 上涨中枢
    DOWN = "DOWN"         # 下跌中枢
    OSCILLATING = "OSCILLATING"  # 震荡中枢

@dataclass
class PriceRange:
    """价格区间"""
    high: float
    low: float
    
    def overlaps_with(self, other: 'PriceRange') -> bool:
        """判断是否与另一个区间重叠"""
        return not (self.high < other.low or self.low > other.high)
    
    def get_overlap(self, other: 'PriceRange') -> Optional['PriceRange']:
        """获取重叠区间"""
        if not self.overlaps_with(other):
            return None
        return PriceRange(
            high=min(self.high, other.high),
            low=max(self.low, other.low)
        )

@dataclass
class Hub:
    """中枢结构"""
    start_time: datetime      # 中枢开始时间
    end_time: datetime        # 中枢结束时间
    zg: float                # 中枢上沿
    zd: float                # 中枢下沿
    hub_type: HubType        # 中枢类型
    strength: int            # 中枢强度（包含的段数）
    
    @property
    def range(self) -> PriceRange:
        """获取中枢范围"""
        return PriceRange(high=self.zg, low=self.zd)
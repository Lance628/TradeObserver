from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from ....models.hub import Hub, HubType, PriceRange
from ....models.candle import Candle
from ..base_analyzer import RealTimeAnalyzer
from ....utils.logger import setup_logger
from ...notifiers.email_notifier import EmailNotifier
from ....database.database import DatabaseManager

class HubAnalyzer(RealTimeAnalyzer):
    def __init__(self, 
                 code: str,
                 period: int,
                 min_candles_for_hub: int = 12,
                 overlap_threshold: float = 0.6,
                 hub_break_threshold: float = 0.3):
        super().__init__()
        self.min_candles_for_hub = min_candles_for_hub
        self.overlap_threshold = overlap_threshold
        self.hub_break_threshold = hub_break_threshold
        
        self.current_hub: Optional[Hub] = None
        self.candles: List[Candle] = []
        self.active_hubs: List[Hub] = []
        self.current_code: Optional[str] = code
        self.period: int = period
        self.email_notifier = EmailNotifier()
        self.db_manager = DatabaseManager()
        
        # 从数据库恢复数据
        self._restore_from_database()
    
    def _restore_from_database(self):
        """从数据库恢复最近的K线数据和中枢状态"""
        try:
            if not self.current_code:
                self.logger.info(f"未找到当前代码{self.current_code}，无法从数据库恢复数据")
                return
                
            # 获取最近30根1分钟K线
            latest_candles = self.db_manager.get_candles(
                code=self.current_code,
                period=1,
                limit=30
            )
            
            if not latest_candles:
                self.logger.info("未找到历史K线数据，将从头开始分析")
                return
                
            # 更新K线列表
            self.candles = latest_candles
            # 尝试在最近的K线中找到中枢
            potential_hub = self._find_hub_in_candles(
                self.candles[-self.min_candles_for_hub:]
            )
            print(potential_hub)
            if potential_hub:
                self.current_hub = potential_hub
                self.active_hubs.append(potential_hub)
                self.logger.info(f"从历史数据中恢复中枢: {potential_hub}")
            
        except Exception as e:
            self.logger.error(f"从数据库恢复数据失败: {str(e)}")
    
    def on_price_update(self, code: str, candle: Candle):
        """接收K线更新"""
        self._analysis_queue.put({
            'code': code,
            'candle': candle,
            'timestamp': datetime.now()
        })
    
    def analyze_data(self, data: dict):
        """处理队列中的数据"""
        self._perform_analysis()
    
    def _perform_analysis(self):
        """执行具体的分析逻辑"""
        # 获取最新K线数据
        latest_candles = self.get_latest_candles(limit=30)
        if not latest_candles:
            return
            
        # 更新K线列表，避免重复
        if not self.candles:
            self.candles = latest_candles
        else:
            # 找到最新的时间戳
            last_timestamp = self.candles[-1].timestamp
            
            # 只添加更新的K线
            new_candles = [
                candle for candle in latest_candles 
                if candle.timestamp > last_timestamp
            ]
            
            if new_candles:
                self.candles.extend(new_candles)
                if len(self.candles) > 100:
                    self.candles = self.candles[-100:]
                self.logger.debug(f"添加了 {len(new_candles)} 根新K线")
        
        # 中枢分析逻辑
        if not self.current_hub:
            self.current_hub = self._find_hub_in_candles(
                self.candles[-self.min_candles_for_hub:]
            )
            if self.current_hub:
                self.active_hubs.append(self.current_hub)
                self.logger.info(f"发现新中枢: {self.current_hub}")
                self._notify_new_hub(self.current_hub)
        
        elif self.current_hub:
            latest_price = latest_candles[-1].close
            if self._is_price_breaking_hub(latest_price, self.current_hub):
                self.logger.info(f"中枢被突破: {self.current_hub}")
                self._notify_hub_break(self.current_hub, latest_price)
                self.current_hub = None
            else:
                self.current_hub.end_time = latest_candles[-1].timestamp
                self.current_hub.strength += 1
    
    def get_latest_candles(self, limit: int = 30) -> List[Candle]:
        """从数据库获取最新的K线数据"""
        try:
            if not self.current_code:
                return []
                
            # 直接从数据库获取1分钟K线数据
            latest_candles = self.db_manager.get_candles(
                code=self.current_code,
                period=1,  # 固定获取1分钟K线
                limit=limit
            )
            
            if not latest_candles:
                self.logger.debug(f"未找到最新K线数据")
                return []
            
            self.logger.debug(f"获取到 {len(latest_candles)} 根K线数据")
            return latest_candles
            
        except Exception as e:
            self.logger.error(f"获取最新K线数据失败: {str(e)}")
            return []
    
    def _get_price_range(self, candles: List[Candle]) -> PriceRange:
        """获取一组K线的价格区间"""
        if not candles:
            return None
        return PriceRange(
            high=max(c.high for c in candles),
            low=min(c.low for c in candles)
        )
    
    def _find_hub_in_candles(self, candles: List[Candle]) -> Optional[Hub]:
        """在一组K线中寻找中枢"""
        if len(candles) < self.min_candles_for_hub:
            return None
        # 将K线分成三段来寻找重叠区域
        segment_size = len(candles) // 3
        seg1 = candles[:segment_size]
        seg2 = candles[segment_size:segment_size*2]
        seg3 = candles[segment_size*2:]
        
        range1 = self._get_price_range(seg1)
        range2 = self._get_price_range(seg2)
        range3 = self._get_price_range(seg3)
        
        # 检查三段是否有重叠
        overlap12 = range1.get_overlap(range2)
        if not overlap12:
            return None
            
        overlap123 = overlap12.get_overlap(range3)
        if not overlap123:
            return None
            
        # 计算重叠区域占比
        total_range = self._get_price_range(candles)
        overlap_ratio = (overlap123.high - overlap123.low) / (total_range.high - total_range.low)
        
        if overlap_ratio < self.overlap_threshold:
            return None
            
        # 确定中枢类型
        hub_type = self._determine_hub_type(candles, overlap123)
        
        return Hub(
            start_time=candles[0].timestamp,
            end_time=candles[-1].timestamp,
            zg=overlap123.high,
            zd=overlap123.low,
            hub_type=hub_type,
            strength=len(candles)
        )
    
    def _determine_hub_type(self, candles: List[Candle], 
                           hub_range: PriceRange) -> HubType:
        """确定中枢类型"""
        # 计算开盘和收盘价的趋势
        opens = [c.open for c in candles]
        closes = [c.close for c in candles]
        
        # 计算趋势线斜率
        open_trend = sum(opens[i] - opens[i-1] for i in range(1, len(opens)))
        close_trend = sum(closes[i] - closes[i-1] for i in range(1, len(closes)))
        
        if open_trend > 0 and close_trend > 0:
            return HubType.UP
        elif open_trend < 0 and close_trend < 0:
            return HubType.DOWN
        else:
            return HubType.OSCILLATING
    
    def _is_price_breaking_hub(self, price: float, hub: Hub) -> bool:
        """判断价格是否突破中枢"""
        hub_height = hub.zg - hub.zd
        
        if price > hub.zg + hub_height * self.hub_break_threshold:
            return True
        if price < hub.zd - hub_height * self.hub_break_threshold:
            return True
            
        return False
    
    def _format_hub_notification(self, hub: Hub) -> str:
        """格式化中枢通知内容"""
        return f"""
发现新的一分钟级别中枢：

中枢类型: {hub.hub_type.value}
中枢上沿: {hub.zg:.3f}
中枢下沿: {hub.zd:.3f}
形成时间: {hub.start_time}
最后更新时间: {hub.end_time}
中枢强度: {hub.strength}

价格区间: {hub.zd:.3f} - {hub.zg:.3f}
波动范围: {((hub.zg - hub.zd) / hub.zd * 100):.2f}%
"""

    def _notify_new_hub(self, hub: Hub):
        """发送新中枢通知"""
        subject = f"新中枢形成通知 - {hub.hub_type.value}"
        content = self._format_hub_notification(hub)
        if not self.email_notifier.send_notification(subject, content):
            # 如果发送失败（达到限制），记录到日志
            self.logger.info(f"新中枢通知未发送（已达到每日限制）: {hub.hub_type.value}")
    
    def _notify_hub_break(self, hub: Hub, break_price: float):
        """发送中枢突破通知"""
        direction = "向上" if break_price > hub.zg else "向下"
        subject = f"中枢突破通知 - {direction}突破"
        content = f"""
中枢被{direction}突破：

突破价格: {break_price:.3f}
原中枢区间: {hub.zd:.3f} - {hub.zg:.3f}
中枢类型: {hub.hub_type.value}
"""
# 中枢持续时间: {(hub.end_time - hub.start_time).seconds // 60}分钟
        
        if not self.email_notifier.send_notification(subject, content):
            self.logger.info(f"中枢突破通知未发送（已达到每日限制）: {direction}突破")
    
    def get_current_hub_status(self) -> dict:
        """获取当前中枢状态"""
        if not self.current_hub:
            return {"status": "无活跃中枢"}
            
        return {
            "status": "活跃中枢",
            "type": self.current_hub.hub_type.value,
            "zg": self.current_hub.zg,
            "zd": self.current_hub.zd,
            "strength": self.current_hub.strength,
            "duration": (self.current_hub.end_time - self.current_hub.start_time).seconds // 60
        }
    
    
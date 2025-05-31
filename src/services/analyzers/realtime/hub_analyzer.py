from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from ....models.hub import Hub, HubType, PriceRange
from ....models.candle import Candle
from ..base_analyzer import RealTimeAnalyzer
from ....utils.logger import setup_logger
from ...notifiers.email_notifier import EmailNotifier
from ....database.database import DatabaseManager
from ....config.settings import HUB_BREAK_PARAMS, DEFAULT_HUB_BREAK_PARAMS

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
        
        # 获取突破参数配置
        break_params = (HUB_BREAK_PARAMS.get(code, {})
                       .get(period, DEFAULT_HUB_BREAK_PARAMS))
        self.up_take_profit = break_params['up_take_profit']
        self.up_stop_loss = break_params['up_stop_loss']
        self.down_take_profit = break_params['down_take_profit']
        self.down_stop_loss = break_params['down_stop_loss']
        
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
                period=self.period,
                limit=100000
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
    
    def on_candle_update(self, code: str, candle: Candle):
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
        latest_candles = self.get_latest_candles(limit=30, period=self.period)
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
                self.logger.debug(f"代码{self.current_code}，周期{self.period}分钟，添加了 {len(new_candles)} 根新K线")
        

        # 中枢分析逻辑
        if not self.current_hub:
            self.current_hub = self._find_hub_in_candles(
                self.candles[-self.min_candles_for_hub:]
            )
            if self.current_hub:
                self.active_hubs.append(self.current_hub)
                self.logger.info(f"代码{self.current_code}，周期{self.period}分钟，发现新中枢: {self.current_hub}")
                self._notify_new_hub(self.current_hub)
        
        elif self.current_hub:
            latest_price = latest_candles[-1].close
            if self._is_price_breaking_hub(latest_price, self.current_hub):
                self.logger.info(f"代码{self.current_code}，周期{self.period}分钟，中枢被突破: {self.current_hub}")
                self._notify_hub_break(self.current_hub, latest_price)
                self.current_hub = None
            else:
                self.current_hub.end_time = latest_candles[-1].timestamp
                self.current_hub.strength += 1
    
    def get_latest_candles(self, limit: int = 30, period: int = 1) -> List[Candle]:
        """从数据库获取最新的K线数据"""
        try:
            if not self.current_code:
                return []
                
            # 直接从数据库获取对应周期的K线数据
            latest_candles = self.db_manager.get_candles(
                code=self.current_code,
                period=period, 
                limit=limit
            )

            
            if not latest_candles:
                self.logger.error(f"未找到最新{self.period}分钟K线数据")
                return []
            
            self.logger.info(f"获取到 {len(latest_candles)} 根{self.period}分钟K线数据")
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
        # print(candles[0].timestamp, candles[-1].timestamp, total_range)
        if total_range.high != total_range.low: 
            overlap_ratio = (overlap123.high - overlap123.low) / (total_range.high - total_range.low)
        else:
            overlap_ratio = 1
        
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
发现新的{self.period}分钟级别中枢：

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
        subject = f"{self.current_code}新{self.period}分钟中枢形成通知 - {hub.hub_type.value}"
        content = self._format_hub_notification(hub)
        if not self.email_notifier.send_notification(subject, content):
            # 如果发送失败（达到限制），记录到日志
            self.logger.info(f"新中枢通知未发送（已达到每日限制）: {hub.hub_type.value}")
    
    def _notify_hub_break(self, hub: Hub, break_price: float):
        """发送中枢突破通知"""
        is_up_break = break_price > hub.zg
        direction = "向上" if is_up_break else "向下"
        
        # 获取对应方向的止盈止损位置
        take_profit = self.up_take_profit if is_up_break else self.down_take_profit
        stop_loss = self.up_stop_loss if is_up_break else self.down_stop_loss
        
        # 计算具体价格
        take_profit_price = break_price * (1 + take_profit)
        stop_loss_price = break_price * (1 + stop_loss)
        
        subject = f"中枢突破通知 - {self.current_code} {direction}突破{self.period}分钟中枢"
        content = f"""
{self.current_code} {self.period}分钟中枢被{direction}突破：

突破价格: {break_price:.3f}
止盈位置: {take_profit_price:.3f} ({take_profit:+.2%})
止损位置: {stop_loss_price:.3f} ({stop_loss:+.2%})
原中枢区间: {hub.zd:.3f} - {hub.zg:.3f}
中枢类型: {hub.hub_type.value}
中枢强度: {hub.strength}
"""
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
    
    def backtest(self, 
                historical_candles: List[Candle], 
                initial_capital: float = 100000.0,
                additional_take_profit: Optional[float] = 0.01,  # 追加仓位止盈比例
                additional_stop_loss: Optional[float] = -0.01,   # 追加仓位止损比例
                reduction_success: Optional[float] = -0.01,      # 减仓成功回补比例
                reduction_fail: Optional[float] = 0.01          # 减仓失败回补比例
                ) -> dict:
        """
        回测中枢分析策略
        
        交易策略：
        1. 第一根K线开盘时建立80%仓位（不设止盈止损）
        2. 向上突破时买入剩余资金的20%（如果启用）：
           - 上涨1%时卖出（止盈）
           - 下跌1%时卖出（止损）
           - 只允许一次追加仓位
        3. 向下跌破时减仓初始仓位的25%（如果启用）：
           - 下跌超过1%时买回（成功）
           - 上涨超过1%时买回（失败）
           - 只允许一次减仓操作

        Args:
            historical_candles: 历史K线数据
            initial_capital: 初始资金
            additional_take_profit: 追加仓位止盈比例，默认1%，None表示禁用追加仓位
            additional_stop_loss: 追加仓位止损比例，默认-1%，None表示禁用追加仓位
            reduction_success: 减仓成功回补比例，默认-1%，None表示禁用减仓
            reduction_fail: 减仓失败回补比例，默认1%，None表示禁用减仓
        """
        self.candles = []
        self.current_hub = None
        self.active_hubs = []
        
        initial_percent = 0
        additional_percent = 0.2
        reduction_percent = 0.25

        # 回测状态
        position = 0  # 持仓数量
        capital = initial_capital  # 当前资金
        trades = []  # 交易记录
        
        # 分别记录初始持仓和追加持仓
        initial_position = 0  # 初始持仓数量
        initial_cost = 0  # 初始持仓成本
        # 追加仓位状态
        has_additional_position = False  # 是否已经进行过追加仓位
        additional_position_info = None  # (买入价格, 持仓数量) 追加仓位记录
        
        # 减仓状态跟踪
        has_reduced_position = False  # 是否已经进行过减仓
        reduced_position_info = None  # (减仓价格, 减仓数量, 减仓金额)
        
        # 检查是否启用追加仓位和减仓功能
        enable_additional = (additional_take_profit is not None and 
                            additional_stop_loss is not None)
        enable_reduction = (reduction_success is not None and 
                           reduction_fail is not None)
        
        # 第一根K线建仓
        first_candle = historical_candles[0]
        initial_position = int(initial_capital * initial_percent / first_candle.open)  # 80%仓位
        if initial_position > 0:
            position = initial_position
            initial_cost = initial_position * first_candle.open
            capital -= initial_cost
            trades.append({
                'time': first_candle.timestamp,
                'type': '买入',
                'price': first_candle.open,
                'shares': initial_position,
                'reason': f'初始建仓({initial_percent:.2%})'
            })
        
        # 模拟真实环境逐K线分析
        for i, candle in enumerate(historical_candles[1:], 1):
            # 更新K线数据
            self.candles.append(candle)
            if len(self.candles) > 100:
                self.candles = self.candles[-100:]
                
            current_price = candle.close
            
            # 检查减仓回补条件
            if enable_reduction and reduced_position_info is not None:
                reduce_price, reduce_shares, reduce_amount = reduced_position_info
                price_change_ratio = (current_price - reduce_price) / reduce_price
                
                # 下跌回补，成功
                if price_change_ratio <= reduction_success:
                    shares_to_buy = int(reduce_amount / current_price)
                    cost = shares_to_buy * current_price
                    if cost <= reduce_amount:
                        position += shares_to_buy
                        capital -= cost
                        effective_shares = min(reduce_shares, shares_to_buy)
                        trades.append({
                            'time': candle.timestamp,
                            'type': '买入',
                            'price': current_price,
                            'shares': shares_to_buy,
                            'reason': f'[减仓][成功] 下跌回补 {price_change_ratio:.2%}',
                            'pnl': effective_shares * (reduce_price - current_price)
                        })
                        reduced_position_info = None
                        has_reduced_position = False
                
                # 上涨回补，失败
                elif price_change_ratio >= reduction_fail:
                    shares_to_buy = int(reduce_amount / current_price)
                    cost = shares_to_buy * current_price
                    if cost <= reduce_amount:
                        position += shares_to_buy
                        capital -= cost
                        effective_shares = min(reduce_shares, shares_to_buy)
                        trades.append({
                            'time': candle.timestamp,
                            'type': '买入',
                            'price': current_price,
                            'shares': shares_to_buy,
                            'reason': f'[减仓][失败] 上涨回补 {price_change_ratio:.2%}',
                            'pnl': effective_shares * (reduce_price - current_price)
                        })
                        reduced_position_info = None
                        has_reduced_position = False
            
            # 检查追加仓位的止盈止损
            if enable_additional and additional_position_info is not None:
                entry_price, shares = additional_position_info
                profit_ratio = (current_price - entry_price) / entry_price
                
                # 止盈逻辑
                if profit_ratio >= additional_take_profit:
                    capital += shares * current_price
                    position -= shares
                    trades.append({
                        'time': candle.timestamp,
                        'type': '卖出',
                        'price': current_price,
                        'shares': shares,
                        'reason': f'[追加仓位][成功] 止盈 {profit_ratio:.2%}',
                        'buy_price': entry_price,
                        'pnl': shares * (current_price - entry_price)
                    })
                    additional_position_info = None
                    has_additional_position = False
                
                # 止损逻辑
                elif profit_ratio <= additional_stop_loss:
                    capital += shares * current_price
                    position -= shares
                    trades.append({
                        'time': candle.timestamp,
                        'type': '卖出',
                        'price': current_price,
                        'shares': shares,
                        'reason': f'[追加仓位][失败] 止损 {profit_ratio:.2%}',
                        'buy_price': entry_price,
                        'pnl': shares * (current_price - entry_price)
                    })
                    additional_position_info = None
                    has_additional_position = False
            
            # 中枢分析和交易逻辑
            if not self.current_hub:
                if len(self.candles) >= self.min_candles_for_hub:
                    potential_hub = self._find_hub_in_candles(
                        self.candles[-self.min_candles_for_hub:]
                    )
                    if potential_hub:
                        self.current_hub = potential_hub
                        self.active_hubs.append(potential_hub)
                        
            # 如果有活跃中枢，检查是否突破
            elif self._is_price_breaking_hub(current_price, self.current_hub):
                if (current_price > self.current_hub.zg and 
                    enable_additional and 
                    not has_additional_position):
                    # 向上突破时买入剩余资金
                    available_capital = capital
                    if available_capital >= current_price:
                        shares = int(available_capital / current_price)
                        cost = shares * current_price
                        if cost <= capital:
                            position += shares
                            capital -= cost
                            has_additional_position = True
                            additional_position_info = (current_price, shares)
                            trades.append({
                                'time': candle.timestamp,
                                'type': '买入',
                                'price': current_price,
                                'shares': shares,
                                'reason': '向上突破追加20%仓位'
                            })
                
                elif (current_price < self.current_hub.zd and 
                      enable_reduction and 
                      not has_reduced_position):
                    # 向下跌破时减仓初始仓位的25%
                    reduce_shares = int(initial_position * reduction_percent)
                    if reduce_shares > 0:
                        position -= reduce_shares
                        reduce_amount = reduce_shares * current_price
                        capital += reduce_amount
                        has_reduced_position = True
                        reduced_position_info = (current_price, reduce_shares, reduce_amount)
                        trades.append({
                            'time': candle.timestamp,
                            'type': '卖出',
                            'price': current_price,
                            'shares': reduce_shares,
                            'reason': f'向下突破减仓{reduction_percent:.2%}',
                            'sell_amount': reduce_amount  # 记录卖出金额
                        })
                
                self.current_hub = None
            else:
                # 更新当前中枢
                self.current_hub.end_time = candle.timestamp
                self.current_hub.strength += 1
        
        # 回测结束，清算所有持仓
        if position > 0:
            final_price = historical_candles[-1].close
            capital += position * final_price
            trades.append({
                'time': historical_candles[-1].timestamp,
                'type': '卖出',
                'price': final_price,
                'shares': position,
                'reason': '回测结束清仓'
            })
        
        # 计算回测结果
        final_value = capital
        total_return = (final_value - initial_capital) / initial_capital * 100
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(trades, historical_candles)
        
        return {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': len(trades),
            'max_drawdown': max_drawdown,
            'trades': trades
        }
    
    def _calculate_max_drawdown(self, trades: List[dict], candles: List[Candle]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0.0
            
        portfolio_values = []
        current_position = 0
        current_capital = trades[0]['price'] * trades[0]['shares']  # 假设第一笔交易是买入
        
        for candle in candles:
            # 更新持仓信息
            for trade in trades:
                if trade['time'] == candle.timestamp:
                    if trade['type'] == '买入':
                        current_position += trade['shares']
                        current_capital -= trade['shares'] * trade['price']
                    else:  # 卖出
                        current_position -= trade['shares']
                        current_capital += trade['shares'] * trade['price']
            
            # 计算当前市值
            portfolio_value = current_capital + (current_position * candle.close)
            portfolio_values.append(portfolio_value)
        
        # 计算最大回撤
        max_drawdown = 0
        peak = portfolio_values[0]
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown * 100  # 转换为百分比
    
    
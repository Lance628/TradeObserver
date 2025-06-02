"""
K线模型单元测试
"""
import pytest
from datetime import datetime
from unittest.mock import patch

from src.models.candle import Candle


class TestCandleModel:
    """测试K线模型功能"""

    @pytest.mark.unit
    def test_candle_creation(self):
        """测试K线对象创建"""
        timestamp = datetime(2024, 1, 15, 9, 30, 0)
        candle = Candle(
            timestamp=timestamp,
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
            amount=103000.0,
            code="588200",
            period=1
        )
        
        assert candle.timestamp == timestamp
        assert candle.open == 100.0
        assert candle.high == 105.0
        assert candle.low == 98.0
        assert candle.close == 103.0
        assert candle.volume == 1000.0
        assert candle.amount == 103000.0
        assert candle.code == "588200"
        assert candle.period == 1

    @pytest.mark.unit
    def test_candle_update_price_higher(self):
        """测试更新价格（更高价格）"""
        candle = Candle(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
            amount=103000.0,
            code="588200",
            period=1
        )
        
        # 更新一个更高的价格
        candle.update(price=107.0, volume=500.0, amount=53500.0)
        
        assert candle.high == 107.0  # 最高价应该更新
        assert candle.low == 98.0    # 最低价不变
        assert candle.close == 107.0  # 收盘价更新
        assert candle.volume == 1500.0  # 成交量累加
        assert candle.amount == 156500.0  # 成交额累加

    @pytest.mark.unit
    def test_candle_update_price_lower(self):
        """测试更新价格（更低价格）"""
        candle = Candle(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
            amount=103000.0,
            code="588200",
            period=1
        )
        
        # 更新一个更低的价格
        candle.update(price=95.0, volume=300.0, amount=28500.0)
        
        assert candle.high == 105.0  # 最高价不变
        assert candle.low == 95.0    # 最低价应该更新
        assert candle.close == 95.0   # 收盘价更新
        assert candle.volume == 1300.0  # 成交量累加
        assert candle.amount == 131500.0  # 成交额累加

    @pytest.mark.unit
    def test_candle_update_price_within_range(self):
        """测试更新价格（在现有范围内）"""
        candle = Candle(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
            amount=103000.0,
            code="588200",
            period=1
        )
        
        # 更新一个在范围内的价格
        candle.update(price=102.0, volume=200.0, amount=20400.0)
        
        assert candle.high == 105.0  # 最高价不变
        assert candle.low == 98.0    # 最低价不变
        assert candle.close == 102.0  # 收盘价更新
        assert candle.volume == 1200.0  # 成交量累加
        assert candle.amount == 123400.0  # 成交额累加


    @pytest.mark.unit
    def test_multiple_updates(self):
        """测试多次更新"""
        candle = Candle(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1000.0,
            amount=103000.0,
            code="588200",
            period=1
        )
        
        # 第一次更新
        candle.update(price=108.0, volume=200.0, amount=21600.0)
        assert candle.high == 108.0
        assert candle.close == 108.0
        assert candle.volume == 1200.0
        
        # 第二次更新
        candle.update(price=96.0, volume=150.0, amount=14400.0)
        assert candle.high == 108.0  # 最高价保持
        assert candle.low == 96.0    # 最低价更新
        assert candle.close == 96.0   # 收盘价更新为最新
        assert candle.volume == 1350.0
        assert candle.amount == 139000.0 
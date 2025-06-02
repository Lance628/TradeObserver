"""
时间工具模块单元测试
"""
import pytest
from datetime import datetime, time, timedelta
from freezegun import freeze_time
from unittest.mock import patch, Mock

from src.utils.time_utils import (
    is_trading_day,
    is_trading_time,
    get_next_trading_time,
    get_market_status,
    get_seconds_to_next_check,
    get_next_valid_day
)


class TestTradingDayCheck:
    """测试交易日判断功能"""

    @pytest.mark.unit
    def test_is_trading_day_workday(self):
        """测试工作日是否为交易日"""
        # 模拟周一工作日
        with patch('src.utils.time_utils.is_workday', return_value=True):
            monday = datetime(2024, 1, 15)  # 周一
            assert is_trading_day(monday) is True

    @pytest.mark.unit
    def test_is_trading_day_weekend(self):
        """测试周末不是交易日"""
        with patch('src.utils.time_utils.is_workday', return_value=False):
            saturday = datetime(2024, 1, 13)  # 周六
            assert is_trading_day(saturday) is False

    @pytest.mark.unit
    def test_is_trading_day_holiday(self):
        """测试节假日不是交易日"""
        with patch('src.utils.time_utils.is_workday', return_value=False):
            holiday = datetime(2024, 1, 1)  # 元旦
            assert is_trading_day(holiday) is False


class TestTradingTimeCheck:
    """测试交易时间判断功能"""

    @pytest.mark.unit
    @freeze_time("2024-01-15 10:30:00")  # 周一上午交易时间
    def test_is_trading_time_morning_session(self):
        """测试早盘交易时间"""
        with patch('src.utils.time_utils.is_workday', return_value=True), \
             patch('src.utils.time_utils.TRADING_HOURS', [
                 {"start": "09:30", "end": "11:30"},
                 {"start": "13:00", "end": "15:00"}
             ]):
            assert is_trading_time() is True

    @pytest.mark.unit
    @freeze_time("2024-01-15 14:30:00")  # 周一下午交易时间
    def test_is_trading_time_afternoon_session(self):
        """测试午盘交易时间"""
        with patch('src.utils.time_utils.is_workday', return_value=True), \
             patch('src.utils.time_utils.TRADING_HOURS', [
                 {"start": "09:30", "end": "11:30"},
                 {"start": "13:00", "end": "15:00"}
             ]):
            assert is_trading_time() is True

    @pytest.mark.unit
    @freeze_time("2024-01-15 12:00:00")  # 周一午休时间
    def test_is_trading_time_lunch_break(self):
        """测试午休时间不是交易时间"""
        with patch('src.utils.time_utils.is_workday', return_value=True), \
             patch('src.utils.time_utils.TRADING_HOURS', [
                 {"start": "09:30", "end": "11:30"},
                 {"start": "13:00", "end": "15:00"}
             ]):
            assert is_trading_time() is False

    @pytest.mark.unit
    @freeze_time("2024-01-13 10:30:00")  # 周六
    def test_is_trading_time_weekend(self):
        """测试周末不是交易时间"""
        with patch('src.utils.time_utils.is_workday', return_value=False):
            assert is_trading_time() is False

    @pytest.mark.unit
    @freeze_time("2024-01-15 16:00:00")  # 周一收盘后
    def test_is_trading_time_after_close(self):
        """测试收盘后不是交易时间"""
        with patch('src.utils.time_utils.is_workday', return_value=True), \
             patch('src.utils.time_utils.TRADING_HOURS', [
                 {"start": "09:30", "end": "11:30"},
                 {"start": "13:00", "end": "15:00"}
             ]):
            assert is_trading_time() is False


class TestMarketStatus:
    """测试市场状态获取功能"""

    @pytest.mark.unit
    @freeze_time("2024-01-15 09:00:00")  # 周一开盘前
    def test_market_status_before_open(self):
        """测试开盘前状态"""
        status = get_market_status()
        assert status == "早盘未开市"

    @pytest.mark.unit
    @freeze_time("2024-01-15 10:30:00")  # 周一早盘
    def test_market_status_morning_session(self):
        """测试早盘交易状态"""
        status = get_market_status()
        assert status == "早盘交易中"

    @pytest.mark.unit
    @freeze_time("2024-01-15 12:00:00")  # 周一午休
    def test_market_status_lunch_break(self):
        """测试午休状态"""
        status = get_market_status()
        assert status == "午间休市"

    @pytest.mark.unit
    @freeze_time("2024-01-15 14:00:00")  # 周一午盘
    def test_market_status_afternoon_session(self):
        """测试午盘交易状态"""
        status = get_market_status()
        assert status == "午盘交易中"

    @pytest.mark.unit
    @freeze_time("2024-01-15 16:00:00")  # 周一收盘后
    def test_market_status_after_close(self):
        """测试收盘后状态"""
        status = get_market_status()
        assert status == "收盘"

    @pytest.mark.unit
    @freeze_time("2024-01-13 10:30:00")  # 周六
    def test_market_status_weekend(self):
        """测试周末状态"""
        status = get_market_status()
        assert status == "周末休市"


class TestNextTradingTime:
    """测试下次交易时间计算功能"""

    @pytest.mark.unit
    @freeze_time("2024-01-15 08:00:00")  # 周一开盘前
    def test_get_next_trading_time_same_day(self):
        """测试当日开盘前获取下次交易时间"""
        next_time = get_next_trading_time()
        expected = datetime(2024, 1, 15, 9, 30, 0)
        assert next_time == expected

    @pytest.mark.unit
    @freeze_time("2024-01-15 16:00:00")  # 周一收盘后
    def test_get_next_trading_time_next_day(self):
        """测试收盘后获取下次交易时间"""
        next_time = get_next_trading_time()
        expected = datetime(2024, 1, 16, 9, 30, 0)
        assert next_time == expected

    @pytest.mark.unit
    @freeze_time("2024-01-13 10:00:00")  # 周六
    def test_get_next_trading_time_weekend(self):
        """测试周末获取下次交易时间"""
        next_time = get_next_trading_time()
        expected = datetime(2024, 1, 15, 9, 30, 0)  # 下周一
        assert next_time == expected


class TestSecondsToNextCheck:
    """测试等待时间计算功能"""

    @pytest.mark.unit
    @freeze_time("2024-01-15 09:29:30")  # 开盘前30秒
    def test_get_seconds_to_next_check_short_wait(self):
        """测试短时间等待"""
        with patch('src.utils.time_utils.get_next_trading_time') as mock_next:
            mock_next.return_value = datetime(2024, 1, 15, 9, 30, 0)
            seconds = get_seconds_to_next_check()
            assert seconds == 30

    @pytest.mark.unit
    @freeze_time("2024-01-13 10:00:00")  # 周六
    def test_get_seconds_to_next_check_long_wait(self):
        """测试长时间等待（超过1小时应返回3600秒）"""
        with patch('src.utils.time_utils.get_next_trading_time') as mock_next:
            mock_next.return_value = datetime(2024, 1, 15, 9, 30, 0)  # 下周一
            seconds = get_seconds_to_next_check()
            assert seconds == 3600

    @pytest.mark.unit
    @freeze_time("2024-01-15 09:30:30")  # 开盘后
    def test_get_seconds_to_next_check_negative(self):
        """测试已经过了时间点的情况"""
        with patch('src.utils.time_utils.get_next_trading_time') as mock_next:
            mock_next.return_value = datetime(2024, 1, 15, 9, 30, 0)  # 已经过了
            seconds = get_seconds_to_next_check()
            assert seconds == 0


class TestNextValidDay:
    """测试下一个有效工作日计算功能"""

    @pytest.mark.unit
    def test_get_next_valid_day_weekday(self):
        """测试工作日获取下一个有效日"""
        monday = datetime(2024, 1, 15)  # 周一
        next_day = get_next_valid_day(monday)
        expected = datetime(2024, 1, 16)  # 周二
        assert next_day.date() == expected.date()

    @pytest.mark.unit
    def test_get_next_valid_day_friday(self):
        """测试周五获取下一个有效日（应跳过周末）"""
        friday = datetime(2024, 1, 12)  # 周五
        next_day = get_next_valid_day(friday)
        expected = datetime(2024, 1, 15)  # 下周一
        assert next_day.date() == expected.date() 
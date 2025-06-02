"""
中枢模型单元测试
"""
import pytest
from datetime import datetime

from src.models.hub import Hub, HubType, PriceRange


class TestPriceRange:
    """测试价格区间功能"""

    @pytest.mark.unit
    def test_price_range_creation(self):
        """测试价格区间创建"""
        price_range = PriceRange(high=105.0, low=95.0)
        assert price_range.high == 105.0
        assert price_range.low == 95.0

    @pytest.mark.unit
    def test_overlaps_with_true(self):
        """测试价格区间重叠（有重叠）"""
        range1 = PriceRange(high=105.0, low=95.0)
        range2 = PriceRange(high=110.0, low=100.0)
        
        assert range1.overlaps_with(range2) is True
        assert range2.overlaps_with(range1) is True

    @pytest.mark.unit
    def test_overlaps_with_false(self):
        """测试价格区间重叠（无重叠）"""
        range1 = PriceRange(high=105.0, low=95.0)
        range2 = PriceRange(high=120.0, low=110.0)
        
        assert range1.overlaps_with(range2) is False
        assert range2.overlaps_with(range1) is False

    @pytest.mark.unit
    def test_overlaps_with_touching(self):
        """测试价格区间重叠（刚好接触）"""
        range1 = PriceRange(high=105.0, low=95.0)
        range2 = PriceRange(high=110.0, low=105.0)
        
        assert range1.overlaps_with(range2) is True
        assert range2.overlaps_with(range1) is True

    @pytest.mark.unit
    def test_get_overlap_with_overlap(self):
        """测试获取重叠区间（有重叠）"""
        range1 = PriceRange(high=105.0, low=95.0)
        range2 = PriceRange(high=110.0, low=100.0)
        
        overlap = range1.get_overlap(range2)
        assert overlap is not None
        assert overlap.high == 105.0
        assert overlap.low == 100.0

    @pytest.mark.unit
    def test_get_overlap_no_overlap(self):
        """测试获取重叠区间（无重叠）"""
        range1 = PriceRange(high=105.0, low=95.0)
        range2 = PriceRange(high=120.0, low=110.0)
        
        overlap = range1.get_overlap(range2)
        assert overlap is None

    @pytest.mark.unit
    def test_get_overlap_identical_ranges(self):
        """测试获取重叠区间（相同区间）"""
        range1 = PriceRange(high=105.0, low=95.0)
        range2 = PriceRange(high=105.0, low=95.0)
        
        overlap = range1.get_overlap(range2)
        assert overlap is not None
        assert overlap.high == 105.0
        assert overlap.low == 95.0


class TestHub:
    """测试中枢模型功能"""

    @pytest.mark.unit
    def test_hub_creation(self):
        """测试中枢对象创建"""
        start_time = datetime(2024, 1, 15, 9, 30, 0)
        end_time = datetime(2024, 1, 15, 10, 30, 0)
        
        hub = Hub(
            start_time=start_time,
            end_time=end_time,
            zg=105.0,
            zd=95.0,
            hub_type=HubType.UP,
            strength=5
        )
        
        assert hub.start_time == start_time
        assert hub.end_time == end_time
        assert hub.zg == 105.0
        assert hub.zd == 95.0
        assert hub.hub_type == HubType.UP
        assert hub.strength == 5

    @pytest.mark.unit
    def test_hub_range_property(self):
        """测试中枢范围属性"""
        hub = Hub(
            start_time=datetime.now(),
            end_time=datetime.now(),
            zg=105.0,
            zd=95.0,
            hub_type=HubType.OSCILLATING,
            strength=3
        )
        
        price_range = hub.range
        assert isinstance(price_range, PriceRange)
        assert price_range.high == 105.0
        assert price_range.low == 95.0

    @pytest.mark.unit
    def test_hub_types(self):
        """测试不同中枢类型"""
        # 上涨中枢
        up_hub = Hub(
            start_time=datetime.now(),
            end_time=datetime.now(),
            zg=105.0,
            zd=95.0,
            hub_type=HubType.UP,
            strength=3
        )
        assert up_hub.hub_type == HubType.UP
        
        # 下跌中枢
        down_hub = Hub(
            start_time=datetime.now(),
            end_time=datetime.now(),
            zg=105.0,
            zd=95.0,
            hub_type=HubType.DOWN,
            strength=4
        )
        assert down_hub.hub_type == HubType.DOWN
        
        # 震荡中枢
        oscillating_hub = Hub(
            start_time=datetime.now(),
            end_time=datetime.now(),
            zg=105.0,
            zd=95.0,
            hub_type=HubType.OSCILLATING,
            strength=6
        )
        assert oscillating_hub.hub_type == HubType.OSCILLATING
        
        # 未确定中枢
        unknown_hub = Hub(
            start_time=datetime.now(),
            end_time=datetime.now(),
            zg=105.0,
            zd=95.0,
            hub_type=HubType.UNKNOWN,
            strength=2
        )
        assert unknown_hub.hub_type == HubType.UNKNOWN

    @pytest.mark.unit
    def test_hub_str_representation(self):
        """测试中枢字符串表示"""
        start_time = datetime(2024, 1, 15, 9, 30, 0)
        end_time = datetime(2024, 1, 15, 10, 30, 0)
        
        hub = Hub(
            start_time=start_time,
            end_time=end_time,
            zg=105.0,
            zd=95.0,
            hub_type=HubType.UP,
            strength=5
        )
        
        str_repr = str(hub)
        assert "Hub(" in str_repr
        assert "start_time='2024-01-15 09:30:00'" in str_repr
        assert "end_time='2024-01-15 10:30:00'" in str_repr
        assert "zg=105.0" in str_repr
        assert "zd=95.0" in str_repr
        assert "hub_type=HubType.UP" in str_repr
        assert "strength=5" in str_repr

    @pytest.mark.unit
    def test_hub_with_different_strengths(self):
        """测试不同强度的中枢"""
        weak_hub = Hub(
            start_time=datetime.now(),
            end_time=datetime.now(),
            zg=105.0,
            zd=95.0,
            hub_type=HubType.OSCILLATING,
            strength=3
        )
        assert weak_hub.strength == 3
        
        strong_hub = Hub(
            start_time=datetime.now(),
            end_time=datetime.now(),
            zg=105.0,
            zd=95.0,
            hub_type=HubType.UP,
            strength=10
        )
        assert strong_hub.strength == 10

    @pytest.mark.unit
    def test_hub_range_interaction(self):
        """测试中枢范围与其他价格区间的交互"""
        hub = Hub(
            start_time=datetime.now(),
            end_time=datetime.now(),
            zg=105.0,
            zd=95.0,
            hub_type=HubType.OSCILLATING,
            strength=5
        )
        
        # 测试与重叠区间的交互
        overlapping_range = PriceRange(high=110.0, low=100.0)
        assert hub.range.overlaps_with(overlapping_range) is True
        
        overlap = hub.range.get_overlap(overlapping_range)
        assert overlap is not None
        assert overlap.high == 105.0
        assert overlap.low == 100.0
        
        # 测试与不重叠区间的交互
        non_overlapping_range = PriceRange(high=120.0, low=110.0)
        assert hub.range.overlaps_with(non_overlapping_range) is False
        assert hub.range.get_overlap(non_overlapping_range) is None 
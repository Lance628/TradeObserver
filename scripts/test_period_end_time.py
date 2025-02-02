import sys
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
sys.path.append('..')  
from datetime import datetime
from src.services.market.candle_manager import CandleManager

def test_period_end_time():
    """测试K线周期结束时间的计算"""
    candle_manager = CandleManager()
    
    # 测试用例列表，格式：(输入时间, 周期(分钟), 预期结束时间)
    test_cases = [
        # 上午交易时段测试
        (
            datetime(2024, 3, 15, 9, 31, 0),  # 9:31
            1,
            datetime(2024, 3, 15, 9, 32, 0)   # 应该结束于 9:32
        ),
        (
            datetime(2024, 3, 15, 9, 45, 30),  # 9:45:30
            5,
            datetime(2024, 3, 15, 9, 50, 0)    # 应该结束于 9:50
        ),
        (
            datetime(2024, 3, 15, 10, 14, 59),  # 10:14:59
            15,
            datetime(2024, 3, 15, 10, 15, 0)    # 应该结束于 10:15
        ),
        
        # 午休时段测试
        (
            datetime(2024, 3, 15, 11, 29, 59),  # 11:29:59
            30,
            datetime(2024, 3, 15, 11, 30, 0)    # 应该结束于 11:30
        ),
        (
            datetime(2024, 3, 15, 12, 30, 0),   # 12:30
            5,
            datetime(2024, 3, 15, 13, 5, 0)    # 应该结束于 11:30（午休时段）
        ),
        
        # 下午交易时段测试
        (
            datetime(2024, 3, 15, 13, 1, 30),   # 13:01:30
            1,
            datetime(2024, 3, 15, 13, 2, 0)     # 应该结束于 13:01
        ),
        (
            datetime(2024, 3, 15, 14, 44, 59),  # 14:44:59
            15,
            datetime(2024, 3, 15, 14, 45, 0)    # 应该结束于 14:45
        ),
        
        # 特殊时间点测试
        (
            datetime(2024, 3, 15, 9, 29, 59),   # 开盘前
            5,
            datetime(2024, 3, 15, 9, 35, 0)     # 应该结束于 9:30（开盘时间）
        ),
        (
            datetime(2024, 3, 15, 15, 1, 0),    # 收盘后
            5,
            datetime(2024, 3, 15, 15, 5, 0)     # 应该结束于 15:00（收盘时间）
        ),
    ]
    
    # 执行测试
    for i, (input_time, period, expected_time) in enumerate(test_cases, 1):
        result = candle_manager._get_period_end_time(input_time, period)
        
        # 验证结果
        if result == expected_time:
            print(f"测试 {i} 通过 ✓")
            print(f"  输入时间: {input_time.strftime('%H:%M:%S')}")
            print(f"  周期: {period}分钟")
            print(f"  预期结束时间: {expected_time.strftime('%H:%M:%S')}")
            print(f"  实际结束时间: {result.strftime('%H:%M:%S')}")
        else:
            print(f"测试 {i} 失败 ✗")
            print(f"  输入时间: {input_time.strftime('%H:%M:%S')}")
            print(f"  周期: {period}分钟")
            print(f"  预期结束时间: {expected_time.strftime('%H:%M:%S')}")
            print(f"  实际结束时间: {result.strftime('%H:%M:%S')}")
        print()

if __name__ == "__main__":
    test_period_end_time() 
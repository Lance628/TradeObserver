from datetime import datetime, time, timedelta
from chinese_calendar import is_workday
from ..config.settings import TRADING_HOURS
from ..utils.logger import setup_logger
import calendar

logger = setup_logger(__name__)

def is_trading_day(date):
    """
    判断是否为交易日
    - 必须是工作日
    - 必须是周一到周五
    """
    return is_workday(date) and date.weekday() < 5

def is_trading_time() -> bool:
    """
    判断当前是否为交易时间
    返回: bool
    """
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    
    # 如果是周末或非工作日，直接返回False
    if current_date.weekday() >= 5 or not is_workday(current_date):
        return False
    
    current_time = current_datetime.time()
    
    # 检查是否在交易时间段内
    for period in TRADING_HOURS:
        start = datetime.strptime(period["start"], "%H:%M").time()
        end = datetime.strptime(period["end"], "%H:%M").time()
        
        if start <= current_time <= end:
            return True
            
    return False

def get_next_trading_time() -> datetime:
    """获取下一个交易时间"""
    now = datetime.now()
    next_time = now
    
    while True:
        try:
            # 如果当前是周末
            if next_time.weekday() >= 5:
                # 移动到下周一
                days_to_monday = 7 - next_time.weekday()
                next_time = next_time.replace(hour=9, minute=30, second=0, microsecond=0)
                next_time += timedelta(days=days_to_monday)
            else:
                # 工作日
                if next_time.time() < datetime.strptime("09:30:00", "%H:%M:%S").time():
                    # 当日开市前
                    next_time = next_time.replace(hour=9, minute=30, second=0, microsecond=0)
                elif next_time.time() > datetime.strptime("15:00:00", "%H:%M:%S").time():
                    # 当日收市后，移到下一个工作日
                    next_time = (next_time + timedelta(days=1)).replace(
                        hour=9, minute=30, second=0, microsecond=0
                    )
                    # 如果下一天是周末，继续循环处理
                    continue
            
            return next_time
            
        except ValueError:
            # 处理月底和年底的情况
            if next_time.month == 12:
                # 年底，转到下一年1月
                next_time = next_time.replace(
                    year=next_time.year + 1,
                    month=1,
                    day=1,
                    hour=9,
                    minute=30,
                    second=0,
                    microsecond=0
                )
            else:
                # 月底，转到下月1号
                next_time = next_time.replace(
                    month=next_time.month + 1,
                    day=1,
                    hour=9,
                    minute=30,
                    second=0,
                    microsecond=0
                )

def get_next_valid_day(current_date: datetime) -> datetime:
    """获取下一个有效的工作日"""
    next_day = current_date + timedelta(days=1)
    
    while True:
        try:
            # 如果是周末，继续往后找
            if next_day.weekday() >= 5:
                next_day += timedelta(days=1)
                continue
                
            return next_day
            
        except ValueError:
            # 处理月底和年底的情况
            if next_day.month == 12:
                next_day = next_day.replace(year=next_day.year + 1, month=1, day=1)
            else:
                next_day = next_day.replace(month=next_day.month + 1, day=1)

def get_market_status() -> str:
    """获取市场状态"""
    now = datetime.now()
    current_time = now.time()
    
    if now.weekday() >= 5:
        return "周末休市"
        
    morning_open = datetime.strptime("09:30:00", "%H:%M:%S").time()
    morning_close = datetime.strptime("11:30:00", "%H:%M:%S").time()
    afternoon_open = datetime.strptime("13:00:00", "%H:%M:%S").time()
    afternoon_close = datetime.strptime("15:00:00", "%H:%M:%S").time()
    
    if current_time < morning_open:
        return "早盘未开市"
    elif morning_open <= current_time <= morning_close:
        return "早盘交易中"
    elif morning_close < current_time < afternoon_open:
        return "午间休市"
    elif afternoon_open <= current_time <= afternoon_close:
        return "午盘交易中"
    else:
        return "收盘"

def get_seconds_to_next_check() -> int:
    """获取到下次检查的秒数"""
    next_time = get_next_trading_time()
    now = datetime.now()
    
    # 计算时间差
    diff = (next_time - now).total_seconds()
    
    # 如果时间差太长（比如周末），最多等待1小时
    if diff > 3600:
        return 3600
        
    # 如果时间差为负，说明已经过了时间点，立即检查
    if diff < 0:
        return 0
        
    return int(diff)

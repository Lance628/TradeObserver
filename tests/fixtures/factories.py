"""
测试数据工厂类 - 使用factory_boy创建测试数据
"""
import factory
from datetime import datetime, timedelta
from factory import Faker


class PriceDataFactory(factory.DictFactory):
    """价格数据工厂"""
    price = factory.Faker('pyfloat', min_value=50, max_value=200, right_digits=2)
    volume = factory.Faker('pyint', min_value=100, max_value=10000)
    amount = factory.LazyAttribute(lambda obj: obj.price * obj.volume)
    change = factory.Faker('pyfloat', min_value=-10, max_value=10, right_digits=2)
    change_percent = factory.LazyAttribute(lambda obj: (obj.change / obj.price) * 100)


class CandleDataFactory(factory.DictFactory):
    """K线数据工厂"""
    open = factory.Faker('pyfloat', min_value=90, max_value=110, right_digits=2)
    high = factory.LazyAttribute(lambda obj: obj.open + factory.Faker('pyfloat', min_value=0, max_value=5, right_digits=2).generate())
    low = factory.LazyAttribute(lambda obj: obj.open - factory.Faker('pyfloat', min_value=0, max_value=5, right_digits=2).generate())
    close = factory.Faker('pyfloat', min_value=90, max_value=110, right_digits=2)
    volume = factory.Faker('pyint', min_value=1000, max_value=50000)
    timestamp = factory.LazyFunction(datetime.now)


class HubDataFactory(factory.DictFactory):
    """中枢数据工厂"""
    start_time = factory.LazyFunction(lambda: datetime.now() - timedelta(hours=1))
    end_time = factory.LazyFunction(datetime.now)
    high = factory.Faker('pyfloat', min_value=100, max_value=110, right_digits=2)
    low = factory.Faker('pyfloat', min_value=90, max_value=100, right_digits=2)
    candle_count = factory.Faker('pyint', min_value=5, max_value=20)


class ETFCodeFactory(factory.Factory):
    """ETF代码工厂"""
    class Meta:
        model = str
    
    code = factory.Iterator(['588200', '588000', '159915', '510300', '510500'])


class TimestampFactory(factory.Factory):
    """时间戳工厂"""
    class Meta:
        model = datetime
    
    # 默认生成最近24小时内的时间戳
    timestamp = factory.Faker('date_time_between', start_date='-1d', end_date='now')


class TradingTimeFactory(factory.Factory):
    """交易时间工厂"""
    class Meta:
        model = datetime
    
    # 生成交易时间段内的时间戳
    timestamp = factory.Faker('date_time_between', 
                            start_date=datetime.now().replace(hour=9, minute=30, second=0, microsecond=0),
                            end_date=datetime.now().replace(hour=15, minute=0, second=0, microsecond=0))


def create_sample_candle_sequence(count=10, code='588200', period='1m'):
    """创建一序列K线数据"""
    candles = []
    base_time = datetime.now().replace(second=0, microsecond=0)
    base_price = 100.0
    
    for i in range(count):
        timestamp = base_time - timedelta(minutes=i)
        price_change = factory.Faker('pyfloat', min_value=-2, max_value=2, right_digits=2).generate()
        
        candle = {
            'timestamp': timestamp,
            'code': code,
            'period': period,
            'open': base_price + price_change,
            'high': base_price + price_change + abs(factory.Faker('pyfloat', min_value=0, max_value=1, right_digits=2).generate()),
            'low': base_price + price_change - abs(factory.Faker('pyfloat', min_value=0, max_value=1, right_digits=2).generate()),
            'close': base_price + price_change + factory.Faker('pyfloat', min_value=-0.5, max_value=0.5, right_digits=2).generate(),
            'volume': factory.Faker('pyint', min_value=1000, max_value=5000).generate()
        }
        candles.append(candle)
        base_price += price_change
    
    return candles 
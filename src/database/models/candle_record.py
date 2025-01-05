from sqlalchemy import Column, Index, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CandleRecord(Base):
    """K线数据库模型"""
    __tablename__ = 'candles'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    code = Column(String(10), nullable=False)
    period = Column(Integer, nullable=False)  # 周期（分钟）
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    
    # 创建索引
    __table_args__ = (
        Index('idx_candle_code_period_time', 'code', 'period', 'timestamp'),
    )
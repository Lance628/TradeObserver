import sys
from datetime import datetime, timedelta
sys.path.append('.')  
from src.services.market.candle_manager import CandleManager
from src.services.analyzers.realtime.hub_analyzer import HubAnalyzer


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='检查并补充缺失的K线数据')
    parser.add_argument('--start', type=str, help='开始日期 (YYYY-MM-DD)', default=None)
    parser.add_argument('--end', type=str, help='结束日期 (YYYY-MM-DD)', default=None)
    
    args = parser.parse_args()
    
    hub_analyzer = HubAnalyzer()
    latest_candles = hub_analyzer.db_manager.get_candles(
        code='588200',
        period=1,  # 固定获取1分钟K线
        limit=30
    )
    print(latest_candles)
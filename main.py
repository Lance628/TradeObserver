import time
from datetime import datetime
from src.services.market.data_fetcher import DataFetcher
from src.services.market.candle_manager import CandleManager
from src.services.analyzers.realtime.hub_analyzer import HubAnalyzer

from src.database.database import DatabaseManager
from src.utils.time_utils import is_trading_time, get_market_status, get_next_trading_time, get_seconds_to_next_check
from src.utils.logger import setup_logger
from src.config.settings import ETF_CODES, FETCH_INTERVAL, EMAIL_CONFIG
from src.services.analyzers.analyzer_manager import AnalyzerManager
from src.services.analyzers.realtime.hub_analyzer import HubAnalyzer


logger = setup_logger("main")

def main():
    # 初始化数据库
    db_manager = DatabaseManager()
    # db_manager.init_database()
    
    data_fetcher = DataFetcher()
    
    # 初始化分析器管理器
    analyzer_manager = AnalyzerManager()
    
    # 确保邮件配置正确
    assert all(EMAIL_CONFIG.values()), "请先配置邮件设置"
    
    # 创建并启动K线管理器
    candle_manager = CandleManager(periods=[1, 5, 15, 30])
    candle_manager.start()
    
    # 创建中枢分析器
    hub_analyzer = HubAnalyzer(
        min_candles_for_hub=12,
        overlap_threshold=0.6,
        hub_break_threshold=0.3
    )
    
    # 启动分析器
    hub_analyzer.start()
    
    analyzer_manager.add_realtime_analyzer(hub_analyzer)
    analyzer_manager.start()
    
    logger.info("ETF监控程序启动")
    
    try:
        while True:
            if not is_trading_time():
                status = get_market_status()
                next_trading = get_next_trading_time()
                wait_seconds = get_seconds_to_next_check()
                
                logger.info(f"市场状态: {status}, {next_trading}")
                logger.info(f"等待 {wait_seconds} 秒后重新检查")
                
                time.sleep(wait_seconds)
                continue
            
            current_time = datetime.now()
            
            for code in ETF_CODES:
                try:
                    price_data = data_fetcher.get_realtime_price(code)
                    if price_data:
                        # 保存原始价格数据
                        db_manager.save_price_data(current_time, code, price_data)
                        
                        # 更新K线数据
                        candle_manager.on_price_update(
                            code=code,
                            timestamp=current_time,
                            price=price_data['price'],
                            volume=price_data['volume'],
                            amount=price_data.get('amount', 0)
                        )
                        
                        # 将数据放入分析队列
                        hub_analyzer.on_price_update(code, price_data)
                        
                        logger.info(f"{code}: 价格={price_data['price']}, "
                                  f"成交量={price_data['volume']}")
                
                except Exception as e:
                    logger.error(f"处理价格数据失败 {code}: {str(e)}")
            
            time.sleep(FETCH_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("程序已停止")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        raise
    finally:
        # 停止所有组件
        hub_analyzer.stop()
        candle_manager.stop()
        candle_manager.join()  # 等待K线管理器线程结束

if __name__ == "__main__":
    # print("ETF监控程序启动")
    main()

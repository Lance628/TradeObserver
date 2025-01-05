import sys
from datetime import datetime, timedelta
sys.path.append('.')  # 添加项目根目录到路径

from src.services.market.candle_manager import CandleManager
from src.config.settings import ETF_CODES
from src.utils.logger import setup_logger

logger = setup_logger("check_missing_candles")

def check_missing_candles(start_date: str = None, end_date: str = None):
    """检查并补充缺失的K线数据
    
    Args:
        start_date: 开始日期，格式：YYYY-MM-DD，默认为昨天
        end_date: 结束日期，格式：YYYY-MM-DD，默认为今天
    """
    # 设置默认日期
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
    if not start_date:
        start_date = end_date - timedelta(days=1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # 转换为datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    logger.info(f"开始检查缺失K线数据: {start_date} 至 {end_date}")
    
    # 创建K线管理器
    candle_manager = CandleManager()
    
    try:
        # 对每个ETF代码检查缺失的K线
        for code in ETF_CODES:
            logger.info(f"正在处理 {code}")
            candle_manager.check_and_save_missing_candles(
                code, 
                start_datetime, 
                end_datetime
            )
            
    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}")
    finally:
        logger.info("检查完成")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='检查并补充缺失的K线数据')
    parser.add_argument('--start', type=str, help='开始日期 (YYYY-MM-DD)', default=None)
    parser.add_argument('--end', type=str, help='结束日期 (YYYY-MM-DD)', default=None)
    
    args = parser.parse_args()
    
    check_missing_candles(args.start, args.end) 
import tushare as ts

from src.config.settings import TUSHARE_TOKEN
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class DataFetcher:
    def __init__(self):
        self._init_tushare()
    
    def _init_tushare(self):
        """初始化Tushare"""
        try:
            ts.set_token(TUSHARE_TOKEN)
            self.pro = ts.pro_api()
            logger.info("Tushare初始化成功")
        except Exception as e:
            logger.error(f"Tushare初始化失败: {str(e)}")
            raise
    
    def get_realtime_price(self, code):
        """获取实时价格数据"""
        try:
            df = ts.get_realtime_quotes(code)
            if df is not None and not df.empty:
                return {
                    'price': float(df['price'][0]),
                    'volume': float(df['volume'][0]),
                    'amount': float(df['amount'][0])
                }
            return None
        except Exception as e:
            logger.error(f"获取{code}数据时出错: {str(e)}")
            return None

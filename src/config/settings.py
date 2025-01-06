from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "data" / "etf_prices.db"
LOG_PATH = BASE_DIR / "logs"

# Tushare配置
TUSHARE_TOKEN = "e8537fb5ca8b4f700997e34289d7406f8481977a86a2af2df26d3b30"

# 监控的ETF代码
ETF_CODES = ['588200']

# 数据获取间隔（秒）
FETCH_INTERVAL = 3

# 交易时间配置
TRADING_HOURS = [
    {"start": "09:30", "end": "11:30"},
    {"start": "13:00", "end": "15:00"}
]

# 邮件配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',  # 或其他邮件服务器
    'smtp_port': 587,
    'sender_email': '774127995@qq.com',
    'sender_password': 'zlmggcflipgmbcbc',  # 对于Gmail，需要使用应用专用密码
    'recipient_email': '774127995@qq.com'
}

# K线周期配置（分钟）
CANDLE_PERIODS = [1, 5, 15, 30]

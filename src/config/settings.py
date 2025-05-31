from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "data" / "etf_prices.db"
LOG_PATH = BASE_DIR / "logs"

# Tushare配置
TUSHARE_TOKEN = "e8537fb5ca8b4f700997e34289d7406f8481977a86a2af2df26d3b30"

# 监控的ETF代码
ETF_CODES = ['588200','513130','159792']

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
CANDLE_PERIODS = [1, 5, 15, 30, 60, 120, 240]

# HubAnalyzer参数配置
# 格式: {code: {period: {参数配置}}}
HUB_ANALYZER_PARAMS = {
    '588200': {
        1: {
            'min_candles_for_hub': 7,
            'overlap_threshold': 0.7,
            'hub_break_threshold': 0.3
        },
        5: {
            'min_candles_for_hub': 9,
            'overlap_threshold': 0.7,
            'hub_break_threshold': 0.3
        }
    },
    '513130': {
        1: {
            'min_candles_for_hub': 5,
            'overlap_threshold': 0.7,
            'hub_break_threshold': 0.3
        },
        5: {
            'min_candles_for_hub': 10,
            'overlap_threshold': 0.7,
            'hub_break_threshold': 0.3
        }
    },
    '159792': {
        1: {
            'min_candles_for_hub': 18,
            'overlap_threshold': 0.7,
            'hub_break_threshold': 0.3
        },
        5: {
            'min_candles_for_hub': 13,
            'overlap_threshold': 0.7,
            'hub_break_threshold': 0.3
        }
    }
}

# 默认参数配置（当特定代码或周期的配置缺失时使用）
DEFAULT_HUB_ANALYZER_PARAMS = {
    'min_candles_for_hub': 8,
    'overlap_threshold': 0.7,
    'hub_break_threshold': 0.3
}

# 中枢突破参数配置
# 格式: {code: {period: {参数配置}}}
HUB_BREAK_PARAMS = {
    '588200': {
        1: {
            'up_take_profit': 0.014,    # 向上突破止盈比例
            'up_stop_loss': -0.008,    # 向上突破止损比例
            'down_take_profit': 0.01,  # 向下突破止盈比例
            'down_stop_loss': -0.005   # 向下突破止损比例
        },
        5: {
            'up_take_profit': 0.008,
            'up_stop_loss': -0.01,
            'down_take_profit': 0.015,
            'down_stop_loss': -0.008
        }
    },
    '513130': {
        1: {
            'up_take_profit': 0.006,
            'up_stop_loss': -0.026,
            'down_take_profit': 0.01,
            'down_stop_loss': -0.005
        },
        5: {
            'up_take_profit': 0.06,
            'up_stop_loss': -0.026,
            'down_take_profit': 0.015,
            'down_stop_loss': -0.008
        }
    },
    '159792': {
        1: {
            'up_take_profit': 0.022,
            'up_stop_loss': -0.03,
            'down_take_profit': 0.01,
            'down_stop_loss': -0.005
        },
        5: {
            'up_take_profit': 0.022,
            'up_stop_loss': -0.028,
            'down_take_profit': 0.015,
            'down_stop_loss': -0.008
        }
    }
}


# 默认突破参数配置
DEFAULT_HUB_BREAK_PARAMS = {
    'up_take_profit': 0.01,
    'up_stop_loss': -0.005,
    'down_take_profit': 0.01,
    'down_stop_loss': -0.005
}

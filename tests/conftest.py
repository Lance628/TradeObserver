"""
pytest配置文件和共享fixtures
"""
import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch
from freezegun import freeze_time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_logger():
    """模拟logger fixture"""
    with patch('src.utils.logger.setup_logger') as mock_setup:
        mock_logger = Mock()
        mock_setup.return_value = mock_logger
        yield mock_logger

@pytest.fixture
def sample_price_data():
    """示例价格数据"""
    return {
        'price': 100.5,
        'volume': 1000,
        'amount': 100500.0,
        'change': 1.5,
        'change_percent': 1.51
    }

@pytest.fixture
def sample_etf_codes():
    """示例ETF代码列表"""
    return ['588200', '588000', '159915']

@pytest.fixture
def trading_time():
    """交易时间fixture"""
    with freeze_time("2024-01-15 10:30:00"):  # 周一上午交易时间
        yield datetime(2024, 1, 15, 10, 30, 0)

@pytest.fixture
def non_trading_time():
    """非交易时间fixture"""
    with freeze_time("2024-01-15 20:30:00"):  # 周一晚上非交易时间
        yield datetime(2024, 1, 15, 20, 30, 0)

@pytest.fixture
def mock_database():
    """模拟数据库连接"""
    with patch('src.database.database.DatabaseManager') as mock_db:
        db_instance = Mock()
        mock_db.return_value = db_instance
        yield db_instance

@pytest.fixture
def mock_data_fetcher():
    """模拟数据获取器"""
    with patch('src.services.market.data_fetcher.DataFetcher') as mock_fetcher:
        fetcher_instance = Mock()
        mock_fetcher.return_value = fetcher_instance
        yield fetcher_instance

@pytest.fixture(autouse=True)
def setup_test_environment():
    """自动设置测试环境"""
    # 设置测试环境变量
    os.environ['TESTING'] = 'true'
    yield
    # 清理
    if 'TESTING' in os.environ:
        del os.environ['TESTING'] 
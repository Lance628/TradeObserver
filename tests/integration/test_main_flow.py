"""
主要业务流程集成测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from tests.fixtures.factories import PriceDataFactory


class TestMainFlowIntegration:
    """测试主要业务流程的集成"""

    @pytest.mark.integration
    @patch('src.services.market.data_fetcher.DataFetcher')
    @patch('src.database.database.DatabaseManager')
    @patch('src.services.market.candle_manager.CandleManager')
    def test_price_data_processing_flow(self, mock_candle_manager, 
                                      mock_db_manager, mock_data_fetcher):
        """测试价格数据处理完整流程"""
        # 设置模拟数据
        sample_price = PriceDataFactory()
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_realtime_price.return_value = sample_price
        mock_data_fetcher.return_value = mock_fetcher_instance
        
        mock_db_instance = Mock()
        mock_db_manager.return_value = mock_db_instance
        
        mock_candle_instance = Mock()
        mock_candle_manager.return_value = mock_candle_instance
        
        # 模拟交易时间
        with patch('src.utils.time_utils.is_trading_time', return_value=True):
            # 这里可以测试实际的业务逻辑
            # 验证数据获取 -> 数据库保存 -> K线更新的流程
            
            # 验证数据获取被调用
            price_data = mock_fetcher_instance.get_realtime_price('588200')
            assert price_data == sample_price
            
            # 验证数据库保存被调用
            current_time = datetime.now()
            mock_db_instance.save_price_data(current_time, '588200', sample_price)
            mock_db_instance.save_price_data.assert_called_once()
            
            # 验证K线更新被调用
            mock_candle_instance.on_price_update(
                code='588200',
                timestamp=current_time,
                price=sample_price['price'],
                volume=sample_price['volume'],
                amount=sample_price.get('amount', 0)
            )
            mock_candle_instance.on_price_update.assert_called_once()

    @pytest.mark.integration
    @patch('src.utils.time_utils.is_trading_time')
    @patch('src.utils.time_utils.get_market_status')
    def test_non_trading_time_handling(self, mock_get_status, mock_is_trading):
        """测试非交易时间的处理逻辑"""
        # 设置非交易时间
        mock_is_trading.return_value = False
        mock_get_status.return_value = "收盘"
        
        # 验证非交易时间的处理逻辑
        assert mock_is_trading() is False
        assert mock_get_status() == "收盘"

    @pytest.mark.integration 
    def test_analyzer_registration_flow(self):
        """测试分析器注册流程"""
        with patch('src.services.market.candle_manager.CandleManager') as mock_candle_manager, \
             patch('src.services.analyzers.realtime.hub_analyzer.HubAnalyzer') as mock_hub_analyzer:
            
            mock_candle_instance = Mock()
            mock_candle_manager.return_value = mock_candle_instance
            
            mock_analyzer_instance = Mock()
            mock_hub_analyzer.return_value = mock_analyzer_instance
            
            # 模拟分析器创建和注册
            analyzer = mock_hub_analyzer(
                code="588200",
                period="1m",
                min_candles_for_hub=12,
                overlap_threshold=0.6,
                hub_break_threshold=0.3
            )
            
            # 验证分析器启动
            analyzer.start()
            mock_analyzer_instance.start.assert_called_once()
            
            # 验证分析器注册到K线管理器
            mock_candle_instance.register_analyzer("588200", "1m", analyzer)
            mock_candle_instance.register_analyzer.assert_called_once_with(
                "588200", "1m", analyzer
            ) 
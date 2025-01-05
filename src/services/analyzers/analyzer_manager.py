import threading
import time
from typing import List
from .base_analyzer import BaseAnalyzer
from ...utils.logger import setup_logger

class AnalyzerManager:
    def __init__(self):
        self.realtime_analyzers: List[BaseAnalyzer] = []
        self.post_market_analyzers: List[BaseAnalyzer] = []
        self.logger = setup_logger(__name__)
        self._stop_flag = False
        self._analyzer_thread = None
    
    def add_realtime_analyzer(self, analyzer: BaseAnalyzer):
        """添加盘中分析器"""
        self.realtime_analyzers.append(analyzer)
    
    def add_post_market_analyzer(self, analyzer: BaseAnalyzer):
        """添加盘后分析器"""
        self.post_market_analyzers.append(analyzer)
    
    def start(self):
        """启动分析器线程"""
        self._stop_flag = False
        self._analyzer_thread = threading.Thread(
            target=self._run_analyzers,
            daemon=True
        )
        self._analyzer_thread.start()
    
    def stop(self):
        """停止分析器线程"""
        self._stop_flag = True
        if self._analyzer_thread:
            self._analyzer_thread.join()
    
    def _run_analyzers(self):
        """运行分析器的主循环"""
        while not self._stop_flag:
            # 运行实时分析器
            for analyzer in self.realtime_analyzers:
                if analyzer.should_analyze():
                    try:
                        analyzer.analyze()
                    except Exception as e:
                        self.logger.error(f"分析器 {analyzer.__class__.__name__} 运行出错: {str(e)}")
            
            # 运行盘后分析器
            for analyzer in self.post_market_analyzers:
                if analyzer.should_analyze():
                    try:
                        analyzer.analyze()
                    except Exception as e:
                        self.logger.error(f"分析器 {analyzer.__class__.__name__} 运行出错: {str(e)}")
            
            time.sleep(1)  # 避免过于频繁的检查
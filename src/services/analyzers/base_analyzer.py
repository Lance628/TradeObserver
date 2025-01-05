from abc import ABC, abstractmethod
from datetime import datetime
from ...utils.logger import setup_logger
from threading import Thread, Event
from queue import Empty, Queue
from typing import Optional

class BaseAnalyzer(ABC):
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    @abstractmethod
    def analyze_data(self, data):
        """执行分析"""
        pass
    
    @abstractmethod
    def should_analyze(self) -> bool:
        """判断是否应该执行分析"""
        pass

class RealTimeAnalyzer(BaseAnalyzer):
    """盘中分析器基类"""
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self._analysis_queue = Queue()
        self._stop_event = Event()
        self._analysis_thread: Optional[Thread] = None
    
    def start(self):
        """启动分析线程"""
        self._stop_event.clear()
        self._analysis_thread = Thread(target=self._analysis_loop, daemon=True)
        self._analysis_thread.start()
        self.logger.info(f"{self.__class__.__name__} 分析线程已启动")
    
    def stop(self):
        """停止分析线程"""
        self._stop_event.set()
        if self._analysis_thread and self._analysis_thread.is_alive():
            self._analysis_thread.join(timeout=5)
        self.logger.info(f"{self.__class__.__name__} 分析线程已停止")
    
    def _analysis_loop(self):
        """分析线程主循环"""
        while not self._stop_event.is_set():
            try:
                # 从队列获取数据，设置超时以便能够响应停止信号
                data = self._analysis_queue.get(timeout=1)
                if data:
                    self.analyze_data(data)
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"分析过程出错: {str(e)}")
    
    def analyze_data(self, data):
        """具体的分析方法，由子类实现"""
        raise NotImplementedError
    
    def should_analyze(self) -> bool:
        """盘中分析器在交易时间内持续运行"""
        from ...utils.time_utils import is_trading_time
        return is_trading_time()

class PostMarketAnalyzer(BaseAnalyzer):
    """盘后分析器基类"""
    def should_analyze(self) -> bool:
        """盘后分析器在收盘后运行一次"""
        # 具体实现可以根据需求调整
        pass
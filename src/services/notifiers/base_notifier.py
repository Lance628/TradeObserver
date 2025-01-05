from abc import ABC, abstractmethod
from ...utils.logger import setup_logger

class BaseNotifier(ABC):
    """通知器基类"""
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    @abstractmethod
    def send_notification(self, subject: str, content: str):
        """发送通知"""
        pass

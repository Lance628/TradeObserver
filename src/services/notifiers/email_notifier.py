import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from .base_notifier import BaseNotifier
from ...config.settings import EMAIL_CONFIG

class EmailNotifier(BaseNotifier):
    def __init__(self):
        super().__init__()
        self.config = EMAIL_CONFIG
        self.daily_limit = 100  # 每日发送限制
        self.sent_count = 0    # 当日已发送数量
        self.last_reset_date = datetime.now().date()  # 上次重置日期
    
    def _check_and_reset_counter(self):
        """检查并在需要时重置计数器"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.sent_count = 0
            self.last_reset_date = current_date
            self.logger.info("邮件发送计数已重置")
    
    def _can_send_email(self) -> bool:
        """检查是否还能发送邮件"""
        self._check_and_reset_counter()
        return self.sent_count < self.daily_limit
    
    def send_notification(self, subject: str, content: str) -> bool:
        """
        发送邮件通知
        返回: 是否发送成功
        """
        if not self._can_send_email():
            self.logger.warning(f"已达到每日发送限制({self.daily_limit}封)，邮件未发送")
            return False
            
        try:
            message = MIMEMultipart()
            message["From"] = self.config['sender_email']
            message["To"] = self.config['recipient_email']
            message["Subject"] = f"{subject} ({self.sent_count + 1}/{self.daily_limit})"
            
            # 添加发送时间和计数信息
            content = f"{content}\n\n" \
                     f"发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                     f"今日已发送：{self.sent_count + 1}/{self.daily_limit}"
            
            message.attach(MIMEText(content, "plain"))
            
            # 连接到SMTP服务器
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(message)
            
            self.sent_count += 1
            self.logger.info(f"邮件通知发送成功: {subject} (今日已发送: {self.sent_count}/{self.daily_limit})")
            return True
            
        except Exception as e:
            self.logger.error(f"发送邮件通知失败: {str(e)}")
            return False

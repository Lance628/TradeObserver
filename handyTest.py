from datetime import date


def main():
    from src.services.notifiers.email_notifier import EmailNotifier
    email_notifier = EmailNotifier()
    email_notifier.send_notification("测试", "测试内容")


if __name__ == "__main__":
    main()

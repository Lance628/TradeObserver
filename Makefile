# TradeObserver项目Makefile

.PHONY: test test-unit test-integration test-coverage install-deps clean help

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  install-deps    - 安装项目依赖"
	@echo "  test           - 运行所有测试"
	@echo "  test-unit      - 只运行单元测试"
	@echo "  test-integration - 只运行集成测试"
	@echo "  test-coverage  - 运行测试并生成覆盖率报告"
	@echo "  clean          - 清理测试生成的文件"

# 安装依赖
install-deps:
	pip install -r requirements.txt

# 运行所有测试
test:
	pytest

# 只运行单元测试
test-unit:
	pytest -m unit

# 只运行集成测试
test-integration:
	pytest -m integration

# 运行测试并生成覆盖率报告
test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# 清理测试生成的文件
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 
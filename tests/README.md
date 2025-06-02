# TradeObserver 测试架构

## 概述

本项目采用分层的测试架构，包含单元测试、集成测试和测试工具。

## 目录结构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                 # pytest配置和共享fixtures
├── README.md                   # 测试架构说明（本文件）
├── unit/                       # 单元测试
│   ├── __init__.py
│   ├── utils/                  # 工具模块测试
│   │   ├── __init__.py
│   │   └── test_time_utils.py  # 时间工具测试
│   ├── models/                 # 模型层测试
│   │   ├── __init__.py
│   │   ├── test_candle.py      # K线模型测试
│   │   └── test_hub.py         # 中枢模型测试
│   └── services/               # 服务层测试
│       └── __init__.py
├── integration/                # 集成测试
│   ├── __init__.py
│   └── test_main_flow.py       # 主要业务流程测试
└── fixtures/                   # 测试数据和工厂
    ├── __init__.py
    └── factories.py            # 测试数据工厂
```

## 测试类型

### 单元测试 (Unit Tests)
- 测试单个函数或类的功能
- 使用 `@pytest.mark.unit` 标记
- 位于 `tests/unit/` 目录下
- 应该快速运行，不依赖外部资源

### 集成测试 (Integration Tests)
- 测试多个组件之间的交互
- 使用 `@pytest.mark.integration` 标记
- 位于 `tests/integration/` 目录下
- 可能需要更多时间运行

## 测试工具

### Fixtures
- 在 `conftest.py` 中定义共享的测试fixtures
- 包括模拟对象、测试数据等

### 工厂类
- 使用 `factory_boy` 创建测试数据
- 位于 `tests/fixtures/factories.py`
- 提供各种模型的测试数据生成

### 时间模拟
- 使用 `freezegun` 进行时间相关测试
- 特别适用于交易时间判断等功能

## 运行测试

### 使用 Makefile（推荐）
```bash
# 查看所有可用命令
make help

# 安装依赖
make install-deps

# 运行所有测试
make test

# 只运行单元测试
make test-unit

# 只运行集成测试
make test-integration

# 运行测试并生成覆盖率报告
make test-coverage

# 清理测试文件
make clean
```

### 直接使用 pytest
```bash
# 运行所有测试
pytest

# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 运行特定文件的测试
pytest tests/unit/utils/test_time_utils.py

# 运行特定测试函数
pytest tests/unit/utils/test_time_utils.py::TestTradingDayCheck::test_is_trading_day_workday

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 测试配置

### pytest.ini
项目根目录的 `pytest.ini` 文件包含了测试配置：
- 测试发现路径
- 覆盖率设置
- 测试标记定义
- 警告过滤

### 覆盖率要求
- 目标覆盖率：80%
- 生成HTML报告到 `htmlcov/` 目录
- 显示缺失覆盖的行

## 编写测试的最佳实践

### 命名规范
- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试函数：`test_*`

### 测试结构
```python
class TestClassName:
    """测试类的功能描述"""
    
    @pytest.mark.unit
    def test_specific_functionality(self):
        """测试特定功能的描述"""
        # Arrange - 准备测试数据
        # Act - 执行被测试的功能
        # Assert - 验证结果
```

### 使用标记
- 为测试添加适当的标记（unit, integration, slow等）
- 使用描述性的测试名称和文档字符串

### Mock使用
- 对外部依赖使用mock
- 使用 `patch` 装饰器或上下文管理器
- 验证mock的调用情况

## 持续集成

测试架构支持CI/CD集成：
- 所有测试都应该能够在无外部依赖的环境中运行
- 使用环境变量 `TESTING=true` 来识别测试环境
- 测试应该是确定性的和可重复的 
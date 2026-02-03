# 年度账单分析工具

整合建设银行、支付宝、微信账单数据，进行去重、分类和统计分析，生成年度消费报告。

## 功能特性

- 支持多平台账单导入（建设银行、支付宝、微信）
- 智能去重：自动识别并去除平台间重复交易
- 中转交易剔除：自动过滤充值、提现、转账等资金流动
- 消费分类：自动识别交易类型并进行分类统计
- 可视化报告：生成多种图表和统计报告

## 安装

使用 UV 管理项目：

```bash
# 安装 UV（如果还没有）
pip install uv

# 同步项目依赖
uv sync
```

## 使用方法

### 1. 准备账单文件

将账单文件放入 `data/input/` 目录：

- 建设银行：`ccb.xlsx`
- 支付宝：`alipay.csv`
- 微信：多个 Excel 文件（`wechat_*.xlsx`）

### 2. 运行分析

```bash
# 激活虚拟环境
uv run python -m bill_analysis.main
```

或使用安装后的命令：

```bash
python -m bill_analysis.main --input-dir data/input --output-dir data/output
```

### 3. 查看报告

生成的报告将保存在 `data/output/` 目录下，包括：

- `cleaned_transactions.csv` - 清洗后的交易数据
- `annual_report.html` - 年度分析报告（含图表）
- `monthly_trend.png` - 月度消费趋势图
- `category_pie.png` - 消费类别饼图

## 项目结构

```
bill_analysis/
├── src/bill_analysis/
│   ├── parsers/        # 账单解析器
│   ├── processors/     # 数据处理（清洗、去重、分类）
│   ├── analyzers/      # 统计分析
│   └── reports/        # 报告生成
├── data/
│   ├── input/          # 输入账单目录
│   └── output/         # 输出报告目录
└── tests/              # 测试代码
```

## 配置选项

可以通过命令行参数调整行为：

- `--input-dir`: 指定输入目录
- `--output-dir`: 指定输出目录
- `--year`: 指定分析年份（默认当年）
- `--format`: 输出格式（html/csv，默认都生成）

## 注意事项

1. 账单文件需要保持原始格式，不要修改列名
2. 金额统一为负数表示支出
3. 时间格式会自动统一为 `YYYY-MM-DD HH:MM:SS`

## 开发

```bash
# 运行测试
uv run pytest

# 代码格式化
uv run black src/
uv run ruff check src/
```

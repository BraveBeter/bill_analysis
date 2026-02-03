# 使用指南

## 快速开始

### 1. 安装依赖

```bash
# 使用 UV 同步依赖
uv sync
```

### 2. 准备账单文件

将你的账单文件放入 `data/input/` 目录：

- **支付宝**: `alipay.csv`
- **微信**: `wechat_2024.xlsx`（支持多个文件，命名格式：`wechat_*.xlsx`）
- **建设银行**: `ccb.xlsx`

#### 支付宝账单导出步骤

1. 打开支付宝 APP
2. 进入「我的」→「账单」
3. 点击右上角「...」→「开具账单流水」
4. 选择时间范围，选择「用于个人对账」
5. 输入邮箱，下载 CSV 格式的账单

#### 微信账单导出步骤

1. 打开微信 APP
2. 进入「我」→「服务」→「钱包」→「账单」
3. 点击「常见问题」→「下载账单」
4. 选择时间范围，选择「用做个人对账」
5. 输入邮箱，下载 Excel 格式的账单

#### 建设银行账单导出步骤

1. 登录建设银行网上银行
2. 进入「账户查询」→「明细查询」
3. 选择时间范围，查询明细
4. 导出为 Excel 格式

### 3. 运行分析

```bash
# 分析当年账单
uv run python -m bill_analysis.main

# 分析指定年份账单
uv run python -m bill_analysis.main --year 2024

# 指定输入输出目录
uv run python -m bill_analysis.main --input-dir data/input --output-dir data/output
```

### 4. 查看报告

分析完成后，在 `data/output/` 目录下会生成：

- `annual_report.html` - 交互式年度消费报告
- `cleaned_transactions.csv` - 清洗后的交易数据
- `category_pie.png` - 消费分类饼图
- `monthly_trend.png` - 月度消费趋势图
- `platform_comparison.png` - 平台消费对比图
- `top_merchants.png` - 消费最多的商户

## 测试示例数据

如果你想先测试一下功能，可以生成示例账单数据：

```bash
uv run python -m bill_analysis.create_sample_data
```

这将在 `data/input/` 目录生成模拟的账单数据，然后你可以运行分析：

```bash
uv run python -m bill_analysis.main --year 2024
```

## 命令行参数

| 参数             | 简写   | 说明               | 默认值           |
|----------------|------|------------------|---------------|
| `--input-dir`  | `-i` | 输入目录             | `data/input`  |
| `--output-dir` | `-o` | 输出目录             | `data/output` |
| `--year`       | `-y` | 分析年份             | 当年            |
| `--days`       | `-d` | 按照天数时间跨度分析       | /             |
| `--all`        | `-a` | 分析input文件夹中的所有数据 | /             |
| `--help`       | /    | 显示帮助             | /             |

## 数据处理说明

### 去重规则

1. **时间 + 金额 + 对方匹配**：去除同一笔交易的重复记录
2. **平台优先级**：微信 > 支付宝 > 建设银行
3. **中转交易剔除**：自动过滤充值、提现、转账等

### 自动分类

系统会根据商品描述和交易对方自动将消费分类为：

- 餐饮美食
- 购物消费
- 交通出行
- 休闲娱乐
- 医疗健康
- 教育培训
- 房屋物业
- 人情往来
- 金融服务

### 数据清洗

- 移除空值和无效记录
- 过滤中转交易（充值、提现等）
- 统一时间格式
- 统一金额符号（支出为负）

## 常见问题

### Q: 为什么有些交易没有被分类？

A: 系统根据关键词自动分类，如果商品描述中没有识别到关键词，会被归类为"未分类"。你可以在导出的 CSV 文件中手动补充分类信息。

### Q: 如何修改分类规则？

A: 分类规则定义在 `src/bill_analysis/processors/classifier.py` 的 `CATEGORY_RULES` 字典中，你可以根据需要添加或修改关键词。

### Q: 支持其他银行吗？

A: 目前只支持建设银行。如果需要添加其他银行，可以参考 `ccb.py` 创建新的解析器类。

### Q: 账单文件格式不匹配怎么办？

A: 不同时间导出的账单格式可能有差异。如果是列名不匹配，可以修改对应解析器中的 `_map_columns` 方法。

## 进阶使用

### 自定义分析

```python
from bill_analysis.main import BillAnalyzer

analyzer = BillAnalyzer(
    input_dir="data/input",
    output_dir="data/output",
    year=2024
)

result = analyzer.run()

# 访问分析结果
transactions = result["transactions"]
analysis = result["analysis"]
```

### 添加自定义分类

```python
from bill_analysis.processors import TransactionClassifier

classifier = TransactionClassifier()

# 添加自定义分类规则
classifier.CATEGORY_RULES["宠物"] = ["宠物", "猫", "狗", "宠物店"]

# 重新编译匹配规则
classifier._compiled_patterns = classifier._compile_patterns()

# 使用自定义分类器
classified = classifier.classify(transactions)
```

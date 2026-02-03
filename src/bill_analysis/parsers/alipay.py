"""支付宝账单解析器"""

import os
import pandas as pd
from .base import BaseParser


class AlipayParser(BaseParser):
    """支付宝账单解析器"""

    def __init__(self):
        super().__init__("支付宝")

    def parse(self, file_path: str) -> pd.DataFrame:
        """
        解析支付宝账单 CSV 文件

        支付宝账单典型列名：
        - 交易时间
        - 交易分类（重要！直接提供分类）
        - 交易对方
        - 对方账号
        - 商品说明
        - 收/支
        - 金额（元）
        - 收/付款方式
        - 交易状态
        - 交易订单号
        - 备注
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"支付宝账单文件不存在: {file_path}")

        # 读取 CSV 文件（支付宝 CSV 可能是 GBK 编码）
        try:
            df = pd.read_csv(file_path, encoding="gbk")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except:
                df = pd.read_csv(file_path, encoding="utf-8-sig")

        # 映射列名到标准格式
        df = self._map_columns(df)

        # 根据交易状态过滤：只保留"交易成功"的交易
        # 这会排除退款成功、交易关闭等状态
        if "交易状态" in df.columns:
            before_count = len(df)
            df = df[df["交易状态"] == "交易成功"].copy()
            after_count = len(df)
            if before_count > after_count:
                print(f"  支付宝账单：根据交易状态过滤，保留 {after_count}/{before_count} 条记录")

        # 标准化数据
        df["时间"] = pd.to_datetime(df["时间"], errors="coerce")
        df["平台"] = self.platform_name

        # 处理金额：移除货币符号并转换
        df["金额"] = pd.to_numeric(df["金额"], errors="coerce").fillna(0)

        # 支付宝中支出已经是负数或需要转换
        df.loc[df["收/支"] == "支出", "金额"] = df.loc[df["收/支"] == "支出", "金额"].abs() * -1
        df.loc[df["收/支"] == "收入", "金额"] = df.loc[df["收/支"] == "收入", "金额"].abs()

        # 标准化分类
        df["分类"] = df["分类"].apply(self._standardize_category)

        # 添加原始描述
        df["原始描述"] = df.get("商品说明", "") + " " + df.get("交易对方", "")

        # 标准化为统一格式
        normalized = self._normalize_dataframe(df)

        return normalized

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        映射支付宝账单列名到标准列名
        """
        # 创建列名映射
        column_mapping = {}

        # 时间列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易时间", "付款时间", "时间"]):
                column_mapping[col] = "时间"
                break

        # 金额列
        for col in df.columns:
            if "金额" in str(col):
                column_mapping[col] = "金额"
                break

        # 交易对方列 -> 映射为"对方"
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易对方", "对方", "商户"]):
                column_mapping[col] = "对方"
                break

        # 交易分类列 -> 映射为"类型"和"分类"
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易分类", "分类"]):
                column_mapping[col] = "分类"
                break

        # 商品说明列 -> 映射为"商品描述"
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["商品说明", "商品名称", "商品"]):
                column_mapping[col] = "商品描述"
                break

        # 收支列
        for col in df.columns:
            if "收/支" in str(col) or "收支" in str(col):
                column_mapping[col] = "收/支"
                break

        # 交易状态列（用于过滤）
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易状态", "状态"]):
                column_mapping[col] = "交易状态"
                break

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保必要的列存在
        if "时间" not in df.columns:
            df["时间"] = df.iloc[:, 0]
        if "金额" not in df.columns:
            raise ValueError("支付宝账单中未找到金额列")
        if "对方" not in df.columns:
            df["对方"] = "未知"
        if "商品描述" not in df.columns:
            df["商品描述"] = ""
        if "分类" not in df.columns:
            df["分类"] = "未分类"
        if "收/支" not in df.columns:
            df["收/支"] = df["金额"].apply(lambda x: "支出" if x < 0 else "收入")
        if "类型" not in df.columns:
            df["类型"] = df.get("分类", "未分类")
        if "交易状态" not in df.columns:
            df["交易状态"] = "交易成功"  # 默认状态，不过滤

        return df[["时间", "金额", "对方", "类型", "商品描述", "分类", "收/支", "交易状态"]]

    def _standardize_category(self, category: str) -> str:
        """
        标准化支付宝消费分类
        """
        if pd.isna(category):
            return "未分类"

        category = str(category).strip()

        # 直接返回已知的正确分类
        known_categories = [
            "餐饮美食", "服饰美容", "生活日用", "交通出行",
            "通信物流", "休闲娱乐", "医疗健康", "教育培训",
            "房屋物业", "水电煤", "投资理财", "转账红包",
            "其他"
        ]

        if category in known_categories:
            return category

        # 分类映射
        category_mapping = {
            "餐饮": "餐饮美食",
            "美食": "餐饮美食",
            "服饰": "服饰美容",
            "美容": "服饰美容",
            "日用": "生活日用",
            "生活": "生活日用",
            "百货": "生活日用",
            "交通": "交通出行",
            "出行": "交通出行",
            "打车": "交通出行",
            "地铁": "交通出行",
            "公交": "交通出行",
            "通信": "通信物流",
            "物流": "通信物流",
            "快递": "通信物流",
            "娱乐": "休闲娱乐",
            "休闲": "休闲娱乐",
            "医疗": "医疗健康",
            "健康": "医疗健康",
            "药店": "医疗健康",
            "医院": "医疗健康",
            "教育": "教育培训",
            "培训": "教育培训",
            "学习": "教育培训",
            "物业": "房屋物业",
            "房租": "房屋物业",
            "住房": "房屋物业",
            "水电": "水电煤",
            "煤气": "水电煤",
            "电费": "水电煤",
            "水费": "水电煤",
            "投资": "投资理财",
            "理财": "投资理财",
            "基金": "投资理财",
            "股票": "投资理财",
            "转账": "转账红包",
            "红包": "转账红包",
        }

        for key, value in category_mapping.items():
            if key in category:
                return value

        return category

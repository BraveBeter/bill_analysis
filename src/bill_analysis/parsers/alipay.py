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

        支付宝账单典型列名（支付宝导出的CSV）：
        - 付款时间
        - 交易分类
        - 交易对方
        - 商品说明
        - 金额（元）
        - 收/支
        - 交易状态
        - 交易来源
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

        # 映射列名
        df = self._map_columns(df)

        # 标准化数据
        df["时间"] = pd.to_datetime(df["时间"], errors="coerce")
        df["平台"] = self.platform_name

        # 处理金额：确保支出为负数
        df["金额"] = pd.to_numeric(df["金额"], errors="coerce").fillna(0)

        # 支付宝中支出已经是负数或需要转换
        # 根据收/支列调整金额符号
        df.loc[df["收/支"] == "支出", "金额"] = df.loc[df["收/支"] == "支出", "金额"].abs() * -1
        df.loc[df["收/支"] == "收入", "金额"] = df.loc[df["收/支"] == "收入", "金额"].abs()

        # 添加原始描述
        df["原始描述"] = df.get("商品说明", "") + " " + df.get("交易对方", "")

        # 标准化为统一格式
        normalized = self._normalize_dataframe(df)

        return normalized

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        映射支付宝账单列名到标准列名

        支付宝列名可能的变体：
        - 付款时间、交易时间
        - 交易分类、分类
        - 交易对方、对方、商户
        - 商品说明、商品名称
        - 金额（元）、金额
        - 收/支
        """
        # 创建列名映射
        column_mapping = {}

        # 时间列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["付款时间", "交易时间", "时间"]):
                column_mapping[col] = "时间"
                break

        # 金额列
        for col in df.columns:
            if "金额" in str(col):
                column_mapping[col] = "金额"
                break

        # 交易对方列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易对方", "对方", "商户"]):
                column_mapping[col] = "交易对方"
                break

        # 分类列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易分类", "分类"]):
                column_mapping[col] = "分类"
                break

        # 商品说明列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["商品说明", "商品名称", "商品"]):
                column_mapping[col] = "商品说明"
                break

        # 收支列
        for col in df.columns:
            if "收/支" in str(col) or "收支" in str(col):
                column_mapping[col] = "收/支"
                break

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保必要的列存在
        if "时间" not in df.columns:
            df["时间"] = df.iloc[:, 0]
        if "金额" not in df.columns:
            raise ValueError("支付宝账单中未找到金额列")
        if "交易对方" not in df.columns:
            df["交易对方"] = "未知"
        if "商品说明" not in df.columns:
            df["商品说明"] = ""
        if "分类" not in df.columns:
            df["分类"] = "未分类"
        if "收/支" not in df.columns:
            df["收/支"] = df["金额"].apply(lambda x: "支出" if x < 0 else "收入")

        return df[["时间", "金额", "交易对方", "分类", "商品说明", "收/支"]]

    def _standardize_category(self, category: str) -> str:
        """
        标准化支付宝消费分类

        支付宝常见分类：
        - 餐饮美食
        - 服饰美容
        - 生活日用
        - 交通出行
        - 通信物流
        - 休闲娱乐
        - 医疗健康
        - 教育培训
        - 房屋物业
        - 水电煤
        - 转账
        - 等等
        """
        if pd.isna(category):
            return "未分类"

        category = str(category).strip()

        # 分类映射
        category_mapping = {
            "餐饮": "餐饮美食",
            "美食": "餐饮美食",
            "服饰": "服饰美容",
            "美容": "服饰美容",
            "日用": "生活日用",
            "生活": "生活日用",
            "交通": "交通出行",
            "出行": "交通出行",
            "通信": "通信物流",
            "物流": "通信物流",
            "快递": "通信物流",
            "娱乐": "休闲娱乐",
            "休闲": "休闲娱乐",
            "医疗": "医疗健康",
            "健康": "医疗健康",
            "药店": "医疗健康",
            "教育": "教育培训",
            "培训": "教育培训",
            "学习": "教育培训",
            "物业": "房屋物业",
            "房租": "房屋物业",
            "水电": "水电煤",
            "煤气": "水电煤",
            "电费": "水电煤",
            "水费": "水电煤",
        }

        for key, value in category_mapping.items():
            if key in category:
                return value

        return category

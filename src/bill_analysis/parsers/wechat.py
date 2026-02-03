"""微信账单解析器"""

import os
import glob
import pandas as pd
from .base import BaseParser


class WechatParser(BaseParser):
    """微信账单解析器"""

    def __init__(self):
        super().__init__("微信")

    def parse(self, file_path: str) -> pd.DataFrame:
        """
        解析微信账单 Excel 文件

        微信账单典型列名：
        - 交易时间
        - 交易类型
        - 交易对方
        - 商品说明
        - 金额（元）
        - 收/支
        - 交易状态
        - 交易单号
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"微信账单文件不存在: {file_path}")

        # 读取 Excel 文件
        df = pd.read_excel(file_path)

        # 映射列名
        df = self._map_columns(df)

        # 标准化数据
        df["时间"] = pd.to_datetime(df["时间"], errors="coerce")
        df["平台"] = self.platform_name

        # 处理金额：移除货币符号后转换为数值
        # 微信账单金额可能包含 ¥, ¥, , 等符号
        df["金额"] = df["金额"].astype(str)
        df["金额"] = df["金额"].str.replace("¥", "", regex=False)
        df["金额"] = df["金额"].str.replace("￥", "", regex=False)
        df["金额"] = df["金额"].str.replace(",", "", regex=False)
        df["金额"] = pd.to_numeric(df["金额"], errors="coerce").fillna(0)

        # 微信中支出已经是负数或需要转换
        df.loc[df["收/支"] == "支出", "金额"] = df.loc[df["收/支"] == "支出", "金额"].abs() * -1
        df.loc[df["收/支"] == "收入", "金额"] = df.loc[df["收/支"] == "收入", "金额"].abs()

        # 添加原始描述
        df["原始描述"] = df.get("商品说明", "") + " " + df.get("交易对方", "")

        # 标准化为统一格式
        normalized = self._normalize_dataframe(df)

        return normalized

    def parse_multiple(self, pattern: str) -> pd.DataFrame:
        """
        解析多个微信账单文件

        Args:
            pattern: 文件匹配模式，如 "data/input/wechat_*.xlsx"

        Returns:
            合并后的交易数据 DataFrame
        """
        files = glob.glob(pattern)

        if not files:
            raise ValueError(f"未找到匹配的微信账单文件: {pattern}")

        dfs = []
        for file_path in files:
            df = self.parse(file_path)
            dfs.append(df)

        # 合并所有数据
        combined = pd.concat(dfs, ignore_index=True)

        # 按时间排序
        combined = combined.sort_values("时间").reset_index(drop=True)

        return combined

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        映射微信账单列名到标准列名

        微信列名可能的变体：
        - 交易时间、交易时间
        - 交易类型、类型
        - 交易对方、对方、商户
        - 商品、商品说明
        - 金额（元）、金额
        - 收/支
        """
        # 创建列名映射
        column_mapping = {}

        # 时间列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易时间", "时间"]):
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

        # 交易类型列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易类型", "类型"]):
                column_mapping[col] = "交易类型"
                break

        # 商品说明列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["商品", "商品说明", "说明"]):
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
            raise ValueError("微信账单中未找到金额列")
        if "交易对方" not in df.columns:
            df["交易对方"] = "未知"
        if "商品说明" not in df.columns:
            df["商品说明"] = ""
        if "交易类型" not in df.columns:
            df["交易类型"] = ""
        if "收/支" not in df.columns:
            df["收/支"] = df["金额"].apply(lambda x: "支出" if x < 0 else "收入")

        return df[["时间", "金额", "交易对方", "交易类型", "商品说明", "收/支"]]

    def _standardize_category(self, category: str) -> str:
        """
        标准化微信消费分类

        微信常见分类：
        - 餐饮
        - 购物
        - 交通
        - 娱乐
        - 医疗
        - 教育
        - 住房
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
            "购物": "购物消费",
            "超市": "购物消费",
            "便利": "购物消费",
            "交通": "交通出行",
            "出行": "交通出行",
            "打车": "交通出行",
            "地铁": "交通出行",
            "公交": "交通出行",
            "娱乐": "休闲娱乐",
            "休闲": "休闲娱乐",
            "电影": "休闲娱乐",
            "游戏": "休闲娱乐",
            "医疗": "医疗健康",
            "药店": "医疗健康",
            "医院": "医疗健康",
            "教育": "教育培训",
            "培训": "教育培训",
            "学习": "教育培训",
            "住房": "房屋物业",
            "房租": "房屋物业",
            "物业": "房屋物业",
            "水电": "水电煤",
            "煤气": "水电煤",
            "电费": "水电煤",
            "水费": "水电煤",
        }

        for key, value in category_mapping.items():
            if key in category:
                return value

        return category

"""建设银行账单解析器"""

import os
import pandas as pd
from .base import BaseParser


class CCBParser(BaseParser):
    """建设银行账单解析器"""

    def __init__(self):
        super().__init__("建设银行")

    def parse(self, file_path: str) -> pd.DataFrame:
        """
        解析建设银行账单 Excel 文件

        建行账单典型列名：
        - 交易时间
        - 交易地点
        - 交易对方
        - 交易金额
        - 账户余额
        - 交易类型
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"建设银行账单文件不存在: {file_path}")

        # 读取 Excel 文件 - 根据文件扩展名选择引擎
        # .xls 文件使用 xlrd 引擎，.xlsx 文件使用 openpyxl 引擎
        engine = "xlrd" if file_path.endswith(".xls") else "openpyxl"
        try:
            df = pd.read_excel(file_path, engine=engine)
        except Exception as e:
            # 如果指定引擎失败，尝试自动选择
            df = pd.read_excel(file_path)

        # 查找关键列（建行列名可能有所不同）
        df = self._map_columns(df)

        # 标准化数据 - 确保金额列为数值类型
        # 处理建设银行特殊的时间格式（YYYYMMDD 整数）
        if "时间" in df.columns:
            # 如果时间是整数格式（YYYYMMDD），需要先转换为字符串
            if pd.api.types.is_integer_dtype(df["时间"]) or df["时间"].dtype == "int64":
                df["时间"] = df["时间"].astype(str)
                df["时间"] = pd.to_datetime(df["时间"], format="%Y%m%d", errors="coerce")
            else:
                df["时间"] = pd.to_datetime(df["时间"], errors="coerce")

        df["金额"] = pd.to_numeric(df["金额"], errors="coerce").fillna(0)
        df["平台"] = self.platform_name
        df["收/支"] = df["金额"].apply(lambda x: "支出" if x < 0 else "收入" if x > 0 else "其他")

        # 添加原始描述
        df["原始描述"] = df.get("交易类型", "") + " " + df.get("交易对方", "")

        # 标准化为统一格式
        normalized = self._normalize_dataframe(df)

        return normalized

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        映射建设银行账单列名到标准列名

        建行列名可能的变体：
        - 交易时间、记账时间、交易日期
        - 交易金额、支出金额、金额
        - 交易对方、收款人、付款人、对方户名
        - 交易类型、交易摘要、摘要
        """
        # 创建列名映射
        column_mapping = {}

        # 时间列 - 优先匹配记账日期
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["记账日期", "记账", "交易日期", "日期", "时间"]):
                column_mapping[col] = "时间"
                break

        # 如果没找到，尝试查找包含日期格式的列
        if "时间" not in column_mapping:
            for col in df.columns:
                if df[col].dtype in ["int64", "object"]:
                    # 检查是否是YYYYMMDD格式的数据
                    sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if sample_val and (
                        (isinstance(sample_val, (int, float)) and 20000000 < sample_val < 21000000) or
                        (isinstance(sample_val, str) and len(sample_val) == 8 and sample_val.isdigit())
                    ):
                        column_mapping[col] = "时间"
                        break

        # 金额列
        for col in df.columns:
            if "金额" in str(col) and "余额" not in str(col):
                column_mapping[col] = "金额"
                break

        # 交易对方列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["对方", "收款人", "付款人", "户名"]):
                column_mapping[col] = "对方"
                break

        # 交易类型列
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["类型", "摘要", "说明"]):
                column_mapping[col] = "交易类型"
                break

        # 商品描述（如果有）
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["商品", "用途", "备注"]):
                column_mapping[col] = "商品描述"
                break

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保必要的列存在
        if "时间" not in df.columns:
            df["时间"] = df.iloc[:, 0]  # 使用第一列作为时间
        if "金额" not in df.columns:
            raise ValueError("建设银行账单中未找到金额列")
        if "对方" not in df.columns:
            df["对方"] = "未知"
        if "商品描述" not in df.columns:
            df["商品描述"] = ""
        if "交易类型" not in df.columns:
            df["交易类型"] = ""

        return df[["时间", "金额", "对方", "交易类型", "商品描述"]]

    def _determine_transaction_type(self, row: pd.Series) -> str:
        """根据交易信息判断交易类型"""
        desc = str(row.get("交易类型", "")) + " " + str(row.get("对方", ""))

        if any(keyword in desc for keyword in ["消费", "支出", "支付"]):
            return "消费"
        elif any(keyword in desc for keyword in ["转账", "转入", "转出"]):
            return "转账"
        elif any(keyword in desc for keyword in ["取现", "提现"]):
            return "提现"
        elif any(keyword in desc for keyword in ["存入", "存款"]):
            return "存款"
        else:
            return "其他"

"""基础账单解析器"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
from datetime import datetime


class BaseParser(ABC):
    """账单解析器基类"""

    def __init__(self, platform_name: str):
        """
        初始化解析器

        Args:
            platform_name: 平台名称（建设银行、支付宝、微信）
        """
        self.platform_name = platform_name

    @abstractmethod
    def parse(self, file_path: str) -> pd.DataFrame:
        """
        解析账单文件

        Args:
            file_path: 账单文件路径

        Returns:
            标准化的交易数据 DataFrame
        """
        pass

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将原始数据标准化为统一格式

        标准字段：
        - 时间: datetime
        - 平台: string
        - 类型: string
        - 对方: string
        - 金额: float (负数表示支出)
        - 收/支: string
        - 商品描述: string
        - 分类: string
        - 原始描述: string
        """
        normalized = pd.DataFrame(
            {
                "时间": pd.to_datetime(df["时间"]),
                "平台": self.platform_name,
                "类型": df.get("类型", ""),
                "对方": df.get("对方", ""),
                "金额": pd.to_numeric(df["金额"], errors="coerce").fillna(0),
                "收/支": df.get("收/支", "支出"),
                "商品描述": df.get("商品描述", ""),
                "分类": df.get("分类", "未分类"),
                "原始描述": df.get("原始描述", ""),
            }
        )

        # 确保支出金额为负数
        normalized.loc[normalized["收/支"] == "支出", "金额"] = normalized.loc[
            normalized["收/支"] == "支出", "金额"
        ].abs() * -1
        # 确保收入金额为正数
        normalized.loc[normalized["收/支"] == "收入", "金额"] = normalized.loc[
            normalized["收/支"] == "收入", "金额"
        ].abs()

        return normalized

    def _standardize_time(self, time_str: str, format_str: Optional[str] = None) -> datetime:
        """
        标准化时间格式

        Args:
            time_str: 时间字符串
            format_str: 时间格式字符串

        Returns:
            标准化的 datetime 对象
        """
        if pd.isna(time_str):
            return datetime.now()

        time_str = str(time_str).strip()

        # 常见时间格式
        formats = [
            format_str,
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
            "%Y年%m月%d日 %H:%M:%S",
            "%Y年%m月%d日",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            if fmt is None:
                continue
            try:
                return datetime.strptime(time_str, fmt)
            except (ValueError, TypeError):
                continue

        # 如果所有格式都失败，尝试用 pandas 解析
        try:
            return pd.to_datetime(time_str)
        except:
            return datetime.now()

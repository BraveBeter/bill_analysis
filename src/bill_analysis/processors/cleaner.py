"""数据清洗模块"""

import pandas as pd
from typing import List


class DataCleaner:
    """数据清洗器"""

    # 中转交易关键词
    TRANSFER_KEYWORDS = [
        "充值",
        "提现",
        "转入",
        "转出",
        "余额",
        "零钱",
        "财付通",
        "支付宝",
        "微信",
        "还款",
        "信用卡",
        "花呗",
        "借呗",
    ]

    def __init__(self):
        """初始化数据清洗器"""
        pass

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗交易数据

        清洗步骤：
        1. 移除空值
        2. 过滤中转交易
        3. 统一数据格式
        4. 移除异常值

        Args:
            df: 原始交易数据

        Returns:
            清洗后的交易数据
        """
        if df.empty:
            return df

        # 复制数据
        cleaned = df.copy()

        # 1. 移除关键列为空的记录
        cleaned = cleaned.dropna(subset=["时间", "金额"])

        # 2. 过滤中转交易
        cleaned = self._filter_transfer_transactions(cleaned)

        # 3. 只保留支出记录（用于消费分析）
        # 如果需要分析收入，可以根据需求修改
        cleaned = cleaned[cleaned["金额"] < 0].copy()

        # 4. 移除金额为0的记录
        cleaned = cleaned[cleaned["金额"] != 0]

        # 5. 移除重复记录（完全相同）
        cleaned = cleaned.drop_duplicates()

        # 重置索引
        cleaned = cleaned.reset_index(drop=True)

        return cleaned

    def _filter_transfer_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        过滤中转交易（充值、提现、转账等）

        Args:
            df: 交易数据

        Returns:
            过滤后的交易数据
        """
        # 过滤条件函数
        def is_transfer_transaction(row: pd.Series) -> bool:
            """判断是否为中转交易"""
            # 检查多个字段
            fields_to_check = ["原始描述", "商品描述", "对方", "类型", "分类"]

            for field in fields_to_check:
                if field in row and pd.notna(row[field]):
                    value = str(row[field]).lower()
                    # 检查是否包含中转关键词
                    for keyword in self.TRANSFER_KEYWORDS:
                        if keyword.lower() in value:
                            return True

            return False

        # 应用过滤
        mask = df.apply(is_transfer_transaction, axis=1)

        # 保留非中转交易
        filtered = df[~mask].copy()

        return filtered

    def remove_by_amount_range(
        self, df: pd.DataFrame, min_amount: float = 0.01, max_amount: float = 1000000
    ) -> pd.DataFrame:
        """
        移除金额范围外的交易

        Args:
            df: 交易数据
            min_amount: 最小金额（绝对值）
            max_amount: 最大金额（绝对值）

        Returns:
            过滤后的交易数据
        """
        mask = (df["金额"].abs() >= min_amount) & (df["金额"].abs() <= max_amount)
        return df[mask].copy()

    def remove_by_time_range(
        self, df: pd.DataFrame, start_time=None, end_time=None
    ) -> pd.DataFrame:
        """
        移除时间范围外的交易

        Args:
            df: 交易数据
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            过滤后的交易数据
        """
        if start_time is not None:
            df = df[df["时间"] >= start_time]

        if end_time is not None:
            df = df[df["时间"] <= end_time]

        return df.copy()

    def normalize_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化分类名称

        Args:
            df: 交易数据

        Returns:
            分类标准化后的数据
        """
        # 定义分类映射
        category_mapping = {
            # 餐饮类
            "餐饮": "餐饮美食",
            "美食": "餐饮美食",
            "吃饭": "餐饮美食",
            "外卖": "餐饮美食",
            # 购物类
            "购物": "购物消费",
            "百货": "购物消费",
            "超市": "购物消费",
            "便利店": "购物消费",
            "服饰": "服饰美容",
            "美妆": "服饰美容",
            "美容": "服饰美容",
            # 交通类
            "交通": "交通出行",
            "出行": "交通出行",
            "打车": "交通出行",
            "地铁": "交通出行",
            "公交": "交通出行",
            "停车": "交通出行",
            "加油": "交通出行",
            # 娱乐类
            "娱乐": "休闲娱乐",
            "休闲": "休闲娱乐",
            "电影": "休闲娱乐",
            "游戏": "休闲娱乐",
            "KTV": "休闲娱乐",
            # 医疗类
            "医疗": "医疗健康",
            "医院": "医疗健康",
            "药店": "医疗健康",
            # 教育类
            "教育": "教育培训",
            "培训": "教育培训",
            "学习": "教育培训",
            # 居住类
            "住房": "房屋物业",
            "房租": "房屋物业",
            "物业": "房屋物业",
            "水电": "水电煤",
            "燃气": "水电煤",
            "水费": "水电煤",
            "电费": "水电煤",
        }

        # 应用映射
        df["分类"] = df["分类"].apply(
            lambda x: category_mapping.get(str(x).strip(), str(x).strip()) if pd.notna(x) else "未分类"
        )

        return df

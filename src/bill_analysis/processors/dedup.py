"""数据去重模块"""

import pandas as pd
from typing import Tuple, List


class Deduplicator:
    """交易去重器"""

    def __init__(self):
        """初始化去重器"""
        # 优先级平台：优先保留微信和支付宝的交易记录
        self.platform_priority = {"微信": 1, "支付宝": 2, "建设银行": 3}

    def deduplicate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        去除重复交易

        去重规则：
        1. 时间 + 金额 + 对方匹配：去除同一笔交易的重复记录
        2. 平台间资金流动去重：优先保留微信/支付宝的交易
        3. 根据平台优先级去重

        Args:
            df: 交易数据

        Returns:
            (去重后的数据, 被移除的重复数据)
        """
        if df.empty:
            return df, pd.DataFrame()

        # 复制数据
        data = df.copy()

        # 生成去重键
        data["dedup_key"] = self._generate_dedup_key(data)

        # 按优先级排序（优先保留高优先级平台）
        data["priority"] = data["平台"].map(self.platform_priority)
        data = data.sort_values("priority")

        # 标记重复项
        data["is_duplicate"] = data.duplicated(subset=["dedup_key"], keep="first")

        # 分离去重后的数据和重复数据
        deduped = data[~data["is_duplicate"]].copy()
        duplicates = data[data["is_duplicate"]].copy()

        # 移除辅助列
        deduped = deduped.drop(columns=["dedup_key", "priority", "is_duplicate"])
        duplicates = duplicates.drop(columns=["dedup_key", "priority", "is_duplicate"])

        # 重置索引
        deduped = deduped.reset_index(drop=True)
        duplicates = duplicates.reset_index(drop=True)

        return deduped, duplicates

    def _generate_dedup_key(self, df: pd.DataFrame) -> pd.Series:
        """
        生成去重键

        去重键基于：时间（精确到分钟）+ 金额 + 对方

        Args:
            df: 交易数据

        Returns:
            去重键 Series
        """
        def make_key(row: pd.Series) -> str:
            # 时间精确到分钟（去除秒的差异）
            time_key = str(row["时间"])[:16] if pd.notna(row["时间"]) else ""

            # 金额（保留2位小数）
            amount_key = f"{abs(float(row['金额'])):.2f}" if pd.notna(row["金额"]) else ""

            # 对方（去除空格）
            party_key = str(row["对方"]).strip() if pd.notna(row["对方"]) else ""

            return f"{time_key}|{amount_key}|{party_key}"

        return df.apply(make_key, axis=1)

    def deduplicate_by_time_window(
        self, df: pd.DataFrame, window_minutes: int = 5
    ) -> pd.DataFrame:
        """
        基于时间窗口去重

        在指定时间窗口内，如果金额和对方相同，视为重复交易

        Args:
            df: 交易数据
            window_minutes: 时间窗口（分钟）

        Returns:
            去重后的数据
        """
        if df.empty:
            return df

        # 按时间排序
        df = df.sort_values("时间").reset_index(drop=True)

        # 标记要删除的行
        to_remove = set()

        for i in range(len(df)):
            if i in to_remove:
                continue

            for j in range(i + 1, len(df)):
                if j in to_remove:
                    continue

                # 计算时间差
                time_diff = (df.loc[j, "时间"] - df.loc[i, "时间"]).total_seconds() / 60

                # 超出时间窗口，停止检查
                if time_diff > window_minutes:
                    break

                # 检查金额和对方是否相同
                if (
                    abs(df.loc[i, "金额"]) == abs(df.loc[j, "金额"])
                    and df.loc[i, "对方"] == df.loc[j, "对方"]
                ):
                    # 比较平台优先级，移除低优先级的
                    priority_i = self.platform_priority.get(df.loc[i, "平台"], 99)
                    priority_j = self.platform_priority.get(df.loc[j, "平台"], 99)

                    if priority_i <= priority_j:
                        to_remove.add(j)
                    else:
                        to_remove.add(i)
                        break

        # 返回去重后的数据
        result = df[~df.index.isin(to_remove)].copy()
        return result.reset_index(drop=True)

    def merge_platform_transfers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        合并平台间资金流动

        如果银行记录显示转账到微信/支付宝，而微信/支付宝记录显示充值，
        则只保留微信/支付宝端的后续消费记录

        Args:
            df: 交易数据

        Returns:
            合并后的数据
        """
        # 这个方法用于识别并标记平台间资金流动
        # 实际的合并逻辑在 DataCleaner 中通过过滤中转交易实现

        # 标记可能的平台间转账
        def is_platform_transfer(row: pd.Series) -> bool:
            desc = str(row.get("原始描述", "")).lower()
            party = str(row.get("对方", "")).lower()

            # 银行转到支付平台
            if row["平台"] == "建设银行":
                if any(keyword in desc or keyword in party for keyword in ["支付宝", "微信", "财付通"]):
                    return True

            # 支付平台提现到银行
            if row["平台"] in ["支付宝", "微信"]:
                if any(keyword in desc for keyword in ["提现", "转入银行", "银行卡"]):
                    return True

            return False

        df["is_platform_transfer"] = df.apply(is_platform_transfer, axis=1)

        return df

    def get_duplicate_summary(self, duplicates: pd.DataFrame) -> dict:
        """
        获取重复交易摘要

        Args:
            duplicates: 被移除的重复数据

        Returns:
            重复交易摘要
        """
        if duplicates.empty:
            return {"total_duplicates": 0, "by_platform": {}}

        summary = {
            "total_duplicates": len(duplicates),
            "total_amount": duplicates["金额"].sum(),
            "by_platform": duplicates.groupby("平台")["金额"].agg(["count", "sum"]).to_dict(),
        }

        return summary

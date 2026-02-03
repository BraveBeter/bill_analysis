"""统计分析模块"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class StatisticsAnalyzer:
    """统计分析器"""

    def __init__(self):
        """初始化统计分析器"""
        pass

    def analyze(
        self,
        df: pd.DataFrame,
        year: Optional[int] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict:
        """
        执行全面分析

        Args:
            df: 交易数据
            year: 分析年份（如果为 None 且未指定 date_range，分析所有数据）
            date_range: 日期范围 (start_date, end_date)，优先级高于 year

        Returns:
            分析结果字典
        """
        if df.empty:
            return self._empty_result()

        # 过滤数据
        df = self._filter_data(df, year, date_range)

        result = {
            "year": year if year else "全部",
            "summary": self._generate_summary(df),
            "by_platform": self._analyze_by_platform(df),
            "by_category": self._analyze_by_category(df),
            "by_month": self._analyze_by_month(df),
            "top_merchants": self._get_top_merchants(df),
        }

        return result

    def _filter_data(
        self,
        df: pd.DataFrame,
        year: Optional[int] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> pd.DataFrame:
        """
        根据年份或日期范围过滤数据

        Args:
            df: 原始交易数据
            year: 年份
            date_range: 日期范围 (start_date, end_date)

        Returns:
            过滤后的数据
        """
        # 优先使用日期范围过滤
        if date_range is not None:
            start_date, end_date = date_range
            return df[(df["时间"] >= start_date) & (df["时间"] <= end_date)].copy()

        # 按年份过滤
        if year is not None:
            return df[df["时间"].dt.year == year].copy()

        # 返回所有数据
        return df.copy()

    def _empty_result(self) -> Dict:
        """返回空结果"""
        return {
            "year": None,
            "summary": {
                "total_transactions": 0,
                "total_amount": 0,
                "average_amount": 0,
                "date_range": (None, None),
            },
            "by_platform": {},
            "by_category": {},
            "by_month": {},
            "top_merchants": [],
        }

    def _generate_summary(self, df: pd.DataFrame) -> Dict:
        """生成摘要统计"""
        total_transactions = len(df)
        total_amount = df["金额"].sum()
        average_amount = df["金额"].mean() if total_transactions > 0 else 0
        min_time = df["时间"].min()
        max_time = df["时间"].max()

        return {
            "total_transactions": total_transactions,
            "total_amount": abs(total_amount),
            "average_amount": abs(average_amount),
            "date_range": (min_time, max_time),
        }

    def _analyze_by_platform(self, df: pd.DataFrame) -> Dict:
        """按平台分析"""
        platform_stats = (
            df.groupby("平台")
            .agg({"金额": ["count", "sum"]})
            .reset_index()
        )

        platform_stats.columns = ["平台", "交易次数", "总金额"]

        result = {}
        for _, row in platform_stats.iterrows():
            result[row["平台"]] = {
                "count": int(row["交易次数"]),
                "amount": abs(float(row["总金额"])),
            }

        return result

    def _analyze_by_category(self, df: pd.DataFrame) -> Dict:
        """按分类分析"""
        category_stats = (
            df.groupby("分类")
            .agg({"金额": ["count", "sum", "mean"]})
            .reset_index()
        )

        category_stats.columns = ["分类", "交易次数", "总金额", "平均金额"]

        # 按总金额降序排序
        category_stats = category_stats.sort_values("总金额", ascending=False)

        result = {}
        for _, row in category_stats.iterrows():
            result[row["分类"]] = {
                "count": int(row["交易次数"]),
                "amount": abs(float(row["总金额"])),
                "average": abs(float(row["平均金额"])),
            }

        return result

    def _analyze_by_month(self, df: pd.DataFrame) -> Dict:
        """按月分析"""
        df_copy = df.copy()
        df_copy["年月"] = df_copy["时间"].dt.to_period("M")

        month_stats = (
            df_copy.groupby("年月")
            .agg({"金额": ["count", "sum"]})
            .reset_index()
        )

        month_stats.columns = ["年月", "交易次数", "总金额"]

        result = {}
        for _, row in month_stats.iterrows():
            period = row["年月"]
            key = f"{period.year}-{period.month:02d}"
            result[key] = {
                "year": period.year,
                "month": period.month,
                "count": int(row["交易次数"]),
                "amount": abs(float(row["总金额"])),
            }

        return result

    def _get_top_merchants(self, df: pd.DataFrame, top_n: int = 20) -> List[Dict]:
        """获取消费最多的商户"""
        merchant_stats = (
            df.groupby("对方")
            .agg({"金额": ["count", "sum"]})
            .reset_index()
        )

        merchant_stats.columns = ["商户", "交易次数", "总金额"]

        merchant_stats["总金额"] = merchant_stats["总金额"].abs()

        merchant_stats = merchant_stats.sort_values("总金额", ascending=False).head(top_n)

        result = []
        for _, row in merchant_stats.iterrows():
            result.append({
                "merchant": row["商户"],
                "count": int(row["交易次数"]),
                "amount": float(row["总金额"]),
            })

        return result

    def detect_anomalies(self, df: pd.DataFrame, threshold_multiplier: float = 2.0) -> List[Dict]:
        """
        检测异常消费

        异常定义：金额超过平均值一定倍数的交易

        Args:
            df: 交易数据
            threshold_multiplier: 阈值倍数

        Returns:
            异常交易列表
        """
        if df.empty:
            return []

        mean_amount = df["金额"].abs().mean()
        std_amount = df["金额"].abs().std()
        threshold = mean_amount + (std_amount * threshold_multiplier)

        anomalies = df[df["金额"].abs() > threshold].copy()

        result = []
        for _, row in anomalies.iterrows():
            result.append({
                "时间": row["时间"],
                "金额": abs(float(row["金额"])),
                "对方": row["对方"],
                "分类": row["分类"],
                "平台": row["平台"],
                "原始描述": row.get("原始描述", ""),
            })

        # 按金额降序排序
        result.sort(key=lambda x: x["金额"], reverse=True)

        return result

    def compare_periods(
        self, df: pd.DataFrame, period1: Tuple, period2: Tuple
    ) -> Dict:
        """
        比较两个时间段的消费

        Args:
            df: 交易数据
            period1: (start_date, end_date) 第一个时间段
            period2: (start_date, end_date) 第二个时间段

        Returns:
            比较结果
        """
        # 过滤两个时间段的数据
        df1 = df[(df["时间"] >= period1[0]) & (df["时间"] <= period1[1])]
        df2 = df[(df["时间"] >= period2[0]) & (df["时间"] <= period2[1])]

        amount1 = df1["金额"].sum()
        amount2 = df2["金额"].sum()
        count1 = len(df1)
        count2 = len(df2)

        change_amount = abs(amount2) - abs(amount1)
        change_percent = (change_amount / abs(amount1) * 100) if amount1 != 0 else 0

        return {
            "period1": {
                "start": period1[0],
                "end": period1[1],
                "amount": abs(amount1),
                "count": count1,
            },
            "period2": {
                "start": period2[0],
                "end": period2[1],
                "amount": abs(amount2),
                "count": count2,
            },
            "change": {
                "amount": change_amount,
                "percent": change_percent,
                "direction": "increase" if change_amount > 0 else "decrease",
            },
        }

    def get_daily_pattern(self, df: pd.DataFrame) -> Dict:
        """
        分析每日消费模式

        Args:
            df: 交易数据

        Returns:
            每日消费模式
        """
        df_copy = df.copy()
        df_copy["日期"] = df_copy["时间"].dt.date
        df_copy["星期"] = df_copy["时间"].dt.dayofweek

        # 按星期统计
        weekday_stats = (
            df_copy.groupby("星期")
            .agg({"金额": ["count", "sum"]})
            .reset_index()
        )

        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        result = {}
        for _, row in weekday_stats.iterrows():
            weekday = int(row["星期"])
            result[weekday] = {
                "name": weekday_names[weekday],
                "count": int(row[("金额", "count")]),
                "amount": abs(float(row[("金额", "sum")])),
            }

        return result

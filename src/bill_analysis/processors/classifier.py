"""交易分类模块"""

import pandas as pd
import re
from typing import Dict, List, Optional


class TransactionClassifier:
    """交易分类器"""

    # 分类规则：关键词映射
    CATEGORY_RULES = {
        "餐饮美食": [
            "餐厅", "饭店", "快餐", "外卖", "美食", "小吃", "火锅", "烧烤",
            "咖啡", "奶茶", "饮品", "点心", "面包", "蛋糕", "零食", "超市",
            "菜市场", "肉", "菜", "水果", "食品", "可口可乐", "百事",
            "星巴克", "瑞幸", "肯德基", "麦当劳", "必胜客", "汉堡王",
            "海底捞", "西贝", "真功夫", "永和大王"
        ],
        "购物消费": [
            "淘宝", "天猫", "京东", "拼多多", "苏宁", "国美", "百货", "商场",
            "超市", "便利店", "服饰", "服装", "鞋", "包", "化妆品", "护肤品",
            "日用品", "家居", "家电", "数码", "手机", "电脑", "相机"
        ],
        "交通出行": [
            "滴滴", "Uber", "出租车", "网约车", "地铁", "公交", "火车", "高铁",
            "飞机", "机票", "船票", "加油", "充电", "停车", "高速", "过路费",
            "租车", "共享单车", "摩拜", "ofo", "哈啰", "美团打车"
        ],
        "休闲娱乐": [
            "电影", "影院", "KTV", "网吧", "游戏", " Steam", "腾讯游戏",
            "网易游戏", "爱奇艺", "腾讯视频", "优酷", "芒果", "哔哩哔哩",
            "音乐", " Spotify", "QQ音乐", "网易云音乐", "健身", "运动",
            "旅游", "景点", "酒店", "民宿", "度假"
        ],
        "医疗健康": [
            "医院", "诊所", "药店", "药房", "挂号", "体检", "疫苗", "医疗",
            "眼镜", "口腔", "牙科", "中医", "按摩", "保健"
        ],
        "教育培训": [
            "教育", "培训", "学校", "课程", "书籍", "图书", "出版社",
            "在线教育", "网课", "辅导", "考试", "学费", "知识付费"
        ],
        "房屋物业": [
            "房租", "物业", "水电", "燃气", "采暖", "宽带", "话费", "充值",
            "联通", "移动", "电信", "水电煤", "维修", "装修", "家具"
        ],
        "人情往来": [
            "红包", "转账", "送礼", "礼物", "礼金", "婚庆", "生日",
            "节日", "春节", "中秋", "国庆"
        ],
        "金融服务": [
            "理财", "基金", "股票", "证券", "保险", "贷款", "还款",
            "信用卡", "花呗", "借呗", "白条", "分期"
        ],
    }

    def __init__(self):
        """初始化分类器"""
        # 编译正则表达式以提高性能
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """编译正则表达式模式"""
        compiled = {}
        for category, keywords in self.CATEGORY_RULES.items():
            compiled[category] = [re.compile(keyword, re.IGNORECASE) for keyword in keywords]
        return compiled

    def classify(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        对交易进行分类

        Args:
            df: 交易数据

        Returns:
            添加了分类的数据
        """
        if df.empty:
            return df

        result = df.copy()

        # 如果已有分类，尝试补充未分类的
        if "分类" in result.columns:
            result["分类"] = result.apply(
                lambda row: row["分类"] if row["分类"] != "未分类" else self._classify_transaction(row),
                axis=1
            )
        else:
            result["分类"] = result.apply(self._classify_transaction, axis=1)

        return result

    def _classify_transaction(self, row: pd.Series) -> str:
        """
        对单笔交易进行分类

        Args:
            row: 交易记录

        Returns:
            分类名称
        """
        # 检查多个字段的组合
        fields_to_check = ["商品描述", "对方", "原始描述", "类型"]

        # 收集所有可能的文本
        combined_text = ""
        for field in fields_to_check:
            if field in row and pd.notna(row[field]):
                combined_text += " " + str(row[field])

        combined_text = combined_text.strip().lower()

        # 按优先级匹配分类
        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(combined_text):
                    return category

        # 如果没有匹配到，返回未分类
        return "未分类"

    def classify_by_amount(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据金额特征进行二次分类

        例如：
        - 整数金额可能是转账
        - 特定金额可能是固定费用

        Args:
            df: 交易数据

        Returns:
            更新分类后的数据
        """
        result = df.copy()

        def adjust_category(row: pd.Series) -> str:
            # 如果已经是明确分类，不调整
            if row["分类"] != "未分类":
                return row["分类"]

            amount = abs(float(row["金额"]))

            # 检查是否为整数（可能是转账或特殊费用）
            if amount == int(amount) and amount > 0:
                # 常见的固定费用
                if amount in [10, 20, 30, 50, 100, 200]:
                    # 可能是充值或固定费用
                    desc = str(row.get("原始描述", "")).lower()
                    if any(keyword in desc for keyword in ["话费", "流量", "充值"]):
                        return "房屋物业"  # 话费归为房屋物业类

            return row["分类"]

        result["分类"] = result.apply(adjust_category, axis=1)

        return result

    def get_category_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        获取分类统计

        Args:
            df: 交易数据

        Returns:
            分类统计 DataFrame
        """
        if "分类" not in df.columns:
            return pd.DataFrame()

        stats = (
            df.groupby("分类")
            .agg({"金额": ["count", "sum", "mean"]})
            .reset_index()
        )

        stats.columns = ["分类", "交易次数", "总金额", "平均金额"]

        # 按总金额降序排序
        stats = stats.sort_values("总金额", ascending=True).reset_index(drop=True)

        return stats

    def merge_categories(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        合并分类

        Args:
            df: 交易数据
            mapping: 分类映射，如 {"餐饮": "餐饮美食", "吃饭": "餐饮美食"}

        Returns:
            合并分类后的数据
        """
        result = df.copy()

        result["分类"] = result["分类"].apply(
            lambda x: mapping.get(str(x), x) if pd.notna(x) else x
        )

        return result

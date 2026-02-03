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
        - 序号
        - 摘要（重要！包含交易类型，如：消费、存入、支取等）
        - 币别
        - 钞汇
        - 交易日期（格式：YYYYMMDD）
        - 交易金额
        - 账户余额
        - 交易地点/附言（重要！包含商户名称等信息）
        - 对方账号与户名
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"建设银行账单文件不存在: {file_path}")

        # 读取 Excel 文件 - 根据文件扩展名选择引擎
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

        # 处理金额：先转换为数值（移除逗号）
        df["金额"] = pd.to_numeric(df["金额"], errors="coerce").fillna(0)

        # 建设银行中：负数=支出，正数=收入
        # 根据金额正负判断收/支（在转换为统一格式前）
        df["收/支"] = df["金额"].apply(lambda x: "支出" if x < 0 else "收入" if x > 0 else "其他")

        # 推断分类
        df["分类"] = df.apply(
            lambda row: self._infer_category(row["类型"], row.get("商品描述", ""), row.get("对方", "")),
            axis=1
        )

        # 添加原始描述
        df["原始描述"] = df.get("类型", "") + " " + df.get("商品描述", "") + " " + df.get("对方", "")

        # 标准化为统一格式
        normalized = self._normalize_dataframe(df)

        return normalized

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        映射建设银行账单列名到标准列名
        """
        # 创建列名映射
        column_mapping = {}

        # 时间列 - 优先匹配记账日期
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["记账日期", "交易日期", "日期", "时间"]):
                column_mapping[col] = "时间"
                break

        # 如果没找到，尝试查找包含日期格式的列
        if "时间" not in column_mapping:
            for col in df.columns:
                if df[col].dtype in ["int64", "object"]:
                    # 检查是否是YYYYMMDD格式的数据
                    sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if sample_val and not pd.isna(sample_val):
                        # 转换为字符串后再检查
                        sample_str = str(sample_val).strip()
                        if (
                            (isinstance(sample_val, (int, float)) and 20000000 < float(sample_val) < 21000000) or
                            (len(sample_str) == 8 and sample_str.isdigit())
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
            if any(keyword in str(col) for keyword in ["对方", "收款人", "付款人", "户名", "对方账号"]):
                column_mapping[col] = "对方"
                break

        # 摘要列 -> 映射为"类型"
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["摘要", "交易类型"]):
                column_mapping[col] = "类型"
                break

        # 交易地点/附言 -> 映射为"商品描述"
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["地点", "附言", "备注", "说明"]):
                column_mapping[col] = "商品描述"
                break

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保必要的列存在
        if "时间" not in df.columns:
            df["时间"] = df.iloc[:, 0]
        if "金额" not in df.columns:
            raise ValueError("建设银行账单中未找到金额列")
        if "对方" not in df.columns:
            df["对方"] = "未知"
        if "类型" not in df.columns:
            df["类型"] = "未知"
        if "商品描述" not in df.columns:
            df["商品描述"] = ""
        # 注意：收/支在 parse 方法中处理，这里不设置
        if "分类" not in df.columns:
            df["分类"] = "未分类"

        return df[["时间", "金额", "对方", "类型", "商品描述", "分类"]]

    def _infer_category(self, summary: str, description: str, counterparty: str) -> str:
        """
        根据摘要、描述和对方推断分类

        Args:
            summary: 交易摘要（如：消费、存入等）
            description: 交易地点/附言
            counterparty: 对方账号与户名
        """
        if pd.isna(summary):
            summary = ""
        if pd.isna(description):
            description = ""
        if pd.isna(counterparty):
            counterparty = ""

        summary = str(summary).strip()
        description = str(description).strip()
        counterparty = str(counterparty).strip()

        # 组合所有信息进行判断
        text = f"{summary} {description} {counterparty}".lower()

        # 根据摘要直接判断
        if "消费" in summary:
            # 进一步判断消费类型
            return self._infer_consumption_type(description, counterparty)

        # 存取款类
        if any(keyword in summary for keyword in ["存入", "存款", "转入"]):
            return "转账红包"  # 存入通常是转账

        if any(keyword in summary for keyword in ["支取", "取现", "提现"]):
            return "其他"  # 取现不计入消费

        # 转账类
        if "转账" in text:
            return "转账红包"

        # 交通出行（优先检查）
        if any(keyword in text for keyword in ["12306", "铁路", "火车票", "高铁",
                                                   "机票", "航空", "飞机", "携程",
                                                   "去哪儿", "同程", "飞猪", "途牛",
                                                   "中铁", "铁旅", "客运"]):
            return "交通出行"

        # 餐饮类
        if any(keyword in text for keyword in ["餐饮", "食堂", "麦当劳", "肯德基",
                                                   "星巴克", "咖啡", "美食", "食品",
                                                   "喜茶", "奈雪", "瑞幸", "必胜客",
                                                   "华莱士", "海底捞", "霸王茶姬",
                                                   "茶百道", "蜜雪冰城", "沪上阿姨"]):
            return "餐饮美食"

        # 超市购物
        if any(keyword in text for keyword in ["超市", "便利店", "百货", "购物",
                                                   "屈臣氏", "沃尔玛", "家乐福",
                                                   "永辉", "盒马", "苏果", "大润发",
                                                   "物美", "ole", "山姆", "美宜佳",
                                                   "罗森", "7-11", "全家"]):
            return "购物消费"

        # 电商平台
        if any(keyword in text for keyword in ["京东", "淘宝", "天猫", "拼多多",
                                                   "抖音", "小红书"]):
            return "购物消费"

        # 生活日用
        if any(keyword in text for keyword in ["日用", "家居", "生活", "零食",
                                                   "有鸣"]):
            return "生活日用"

        # 交通类
        if any(keyword in text for keyword in ["交通", "出行", "停车", "加油",
                                                   "地铁", "公交", "打车", "骑车",
                                                   "哈啰", "青桔", "美团骑行", "摩拜"]):
            return "交通出行"

        # 话费充值
        if any(keyword in text for keyword in ["话费", "充值", "通讯", "宽带",
                                                   "移动", "联通", "电信"]):
            return "通讯话费"

        # 娱乐
        if any(keyword in text for keyword in ["电影", "ktv", "游戏", "视频",
                                                   "音乐", "娱乐", "腾讯视频",
                                                   "爱奇艺", "优酷", "bilibili",
                                                   "抖音", "快手"]):
            return "休闲娱乐"

        # 教育类
        if any(keyword in text for keyword in ["教育", "培训", "学习", "课程",
                                                   "书店"]):
            return "教育培训"

        # 医疗类
        if any(keyword in text for keyword in ["医院", "药店", "诊所", "医疗",
                                                   "健康", "药房", "体检"]):
            return "医疗健康"

        # 支付宝/微信消费
        if "支付宝" in text or "微信" in text:
            # 从描述中提取商户类型
            return self._infer_consumption_type(description, counterparty)

        return "未分类"

    def _infer_consumption_type(self, description: str, counterparty: str) -> str:
        """从消费描述推断具体类型"""
        text = f"{description} {counterparty}".lower()

        # 交通出行（优先检查）
        if any(kw in text for kw in ["12306", "铁路", "火车票", "高铁", "机票",
                                      "航空", "飞机", "携程", "去哪儿", "同程",
                                      "飞猪", "途牛", "马蜂窝", "中铁", "铁旅",
                                      "客运"]):
            return "交通出行"

        # 地铁公交打车
        if any(kw in text for kw in ["地铁", "公交", "打车", "滴滴", "出租车",
                                      "骑车", "单车", "停车", "加油", "充电",
                                      "哈啰", "青桔", "美团骑行", "摩拜"]):
            return "交通出行"

        # 餐饮
        if any(kw in text for kw in ["餐", "饮", "咖啡", "茶", "麦当劳", "肯德基",
                                      "星巴克", "汉堡", "披萨", "美食", "食品", "食堂",
                                      "喜茶", "奈雪", "瑞幸", "必胜客", "华莱士",
                                      "海底捞", "霸王茶姬", "茶百道", "蜜雪冰城",
                                      "沪上阿姨"]):
            return "餐饮美食"

        # 超市购物
        if any(kw in text for kw in ["超市", "便利店", "屈臣氏", "沃尔玛", "家乐福",
                                      "永辉", "盒马", "百货", "购物", "苏果", "大润发",
                                      "物美", "ole", "山姆", "美宜佳", "罗森",
                                      "7-11", "全家"]):
            return "购物消费"

        # 电商平台
        if any(kw in text for kw in ["京东", "淘宝", "天猫", "拼多多", "抖音",
                                      "小红书", "苏宁", "国美"]):
            return "购物消费"

        # 生活日用
        if any(kw in text for kw in ["日用", "家居", "生活", "零食", "有鸣"]):
            return "生活日用"

        # 服饰美容
        if any(kw in text for kw in ["服装", "服饰", "鞋", "帽", "美容", "美发",
                                      "美甲", "化妆", "bag", "shop", "store",
                                      "护肤品"]):
            return "服饰美容"

        # 娱乐
        if any(kw in text for kw in ["电影", "ktv", "游戏", "视频", "音乐", "娱乐",
                                      "腾讯视频", "爱奇艺", "优酷", "bilibili",
                                      "抖音", "快手"]):
            return "休闲娱乐"

        # 通讯
        if any(kw in text for kw in ["话费", "充值", "通讯", "宽带", "流量",
                                      "移动", "联通", "电信"]):
            return "通讯话费"

        # 教育
        if any(kw in text for kw in ["教育", "培训", "学习", "课程", "书店"]):
            return "教育培训"

        # 医疗
        if any(kw in text for kw in ["医院", "药店", "诊所", "医疗", "健康",
                                      "药房", "体检"]):
            return "医疗健康"

        return "购物消费"  # 默认归类为购物消费

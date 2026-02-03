"""微信账单解析器"""

import os
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
        - 交易类型（重要！直接提供类型）
        - 交易对方（重要！直接提供对方）
        - 商品
        - 收/支
        - 金额(元)
        - 支付方式
        - 当前状态
        - 交易单号
        - 商户单号
        - 备注
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"微信账单文件不存在: {file_path}")

        # 读取 Excel 文件
        df = pd.read_excel(file_path)

        # 映射列名
        df = self._map_columns(df)

        # 根据交易状态过滤：只保留"支付成功"的交易
        # 这会排除已退款、已退款(￥X)、已全额退款等状态
        if "交易状态" in df.columns:
            before_count = len(df)
            df = df[df["交易状态"] == "支付成功"].copy()
            after_count = len(df)
            if before_count > after_count:
                print(f"  微信账单：根据交易状态过滤，保留 {after_count}/{before_count} 条记录")

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

        # 标准化分类
        df["分类"] = df.apply(
            lambda row: self._infer_category(row["类型"], row["对方"], row.get("商品描述", "")),
            axis=1
        )

        # 添加原始描述
        df["原始描述"] = df.get("商品描述", "") + " " + df.get("对方", "")

        # 标准化为统一格式
        normalized = self._normalize_dataframe(df)

        return normalized

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        映射微信账单列名到标准列名
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

        # 交易对方列 -> 映射为"对方"
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易对方", "对方", "商户"]):
                column_mapping[col] = "对方"
                break

        # 交易类型列 -> 映射为"类型"
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["交易类型", "类型"]):
                column_mapping[col] = "类型"
                break

        # 商品列 -> 映射为"商品描述"
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["商品", "商品说明", "说明"]):
                column_mapping[col] = "商品描述"
                break

        # 收支列
        for col in df.columns:
            if "收/支" in str(col) or "收支" in str(col):
                column_mapping[col] = "收/支"
                break

        # 交易状态列（用于过滤）
        for col in df.columns:
            if any(keyword in str(col) for keyword in ["当前状态", "状态"]):
                column_mapping[col] = "交易状态"
                break

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保必要的列存在
        if "时间" not in df.columns:
            df["时间"] = df.iloc[:, 0]
        if "金额" not in df.columns:
            raise ValueError("微信账单中未找到金额列")
        if "对方" not in df.columns:
            df["对方"] = "未知"
        if "类型" not in df.columns:
            df["类型"] = "未知"
        if "商品描述" not in df.columns:
            df["商品描述"] = ""
        if "收/支" not in df.columns:
            df["收/支"] = df["金额"].apply(lambda x: "支出" if x < 0 else "收入")
        if "分类" not in df.columns:
            df["分类"] = "未分类"
        if "交易状态" not in df.columns:
            df["交易状态"] = "支付成功"  # 默认状态，不过滤

        return df[["时间", "金额", "对方", "类型", "商品描述", "分类", "收/支", "交易状态"]]

    def _infer_category(self, trans_type: str, counterparty: str, product: str) -> str:
        """
        根据交易类型、对方和商品描述推断分类

        Args:
            trans_type: 交易类型（如：商户消费、转账等）
            counterparty: 交易对方
            product: 商品描述
        """
        if pd.isna(trans_type):
            trans_type = ""
        if pd.isna(counterparty):
            counterparty = ""
        if pd.isna(product):
            product = ""

        trans_type = str(trans_type).strip()
        counterparty = str(counterparty).strip()
        product = str(product).strip()

        # 组合所有信息进行判断
        text = f"{trans_type} {counterparty} {product}".lower()

        # 转账类
        if "转账" in trans_type or "转账" in text:
            return "转账红包"

        # 红包类
        if "红包" in text:
            return "转账红包"

        # 交通出行类（优先检查，因为12306等很重要）
        if any(keyword in text for keyword in ["12306", "铁路", "火车票", "高铁",
                                                   "机票", "航空", "飞机", "携程", "去哪儿",
                                                   "同程", "飞猪", "途牛", "马蜂窝",
                                                   "中铁网络", "铁旅科技", "客运"]):
            return "交通出行"

        # 地铁公交打车
        if any(keyword in text for keyword in ["地铁", "公交", "打车", "滴滴", "出租车",
                                                   "骑车", "单车", "停车", "加油", "充电",
                                                   "哈啰", "青桔", "美团骑行", "摩拜"]):
            return "交通出行"

        # 教育类（优先检查，避免与"料理"等词冲突）
        if any(keyword in text for keyword in ["大学", "学院", "学校", "教育", "培训",
                                                   "学习", "课程", "书店", "考试", "报名",
                                                   "学而思", "新东方", "网易云课堂",
                                                   "慕课", "腾讯课堂", "打印"]):
            return "教育培训"

        # 餐饮类（包含串串、火锅等中餐，避免使用"理"单独匹配）
        if any(keyword in text for keyword in ["麦当劳", "肯德基", "星巴克", "咖啡", "奶茶",
                                                   "餐饮", "美食", "食品", "外卖", "饿了么",
                                                   "美团", "饿了么", "喜茶", "奈雪", "瑞幸",
                                                   "必胜客", "汉堡王", "华莱士", "海底捞",
                                                   "霸王茶姬", "茶百道", "蜜雪冰城", "沪上阿姨",
                                                   "串串", "火锅", "烧烤", "烤肉",
                                                   "小吃", "面馆", "米粉", "麻辣烫",
                                                   "料理店", "日本料理", "韩国料理"]):
            return "餐饮美食"

        # 购物类（增加"超级市场"等关键词）
        if any(keyword in text for keyword in ["超市", "便利店", "超级市场", "卖场",
                                                   "京东", "淘宝", "天猫", "拼多多",
                                                   "购物", "百货", "服装", "电器",
                                                   "永辉", "盒马", "屈臣氏", "沃尔玛", "家乐福",
                                                   "苏果", "大润发", "物美", "ole", "山姆",
                                                   "壹度", "苏宁", "国美", "华润"]):
            return "购物消费"

        # 生活日用类
        if any(keyword in text for keyword in ["便利", "百货", "日用", "家居", "生活",
                                                   "美宜佳", "罗森", "7-11", "全家",
                                                   "零食", "有鸣", "售货机", "文体",
                                                   "文体店", "电动车"]):
            return "生活日用"

        # 通讯充值
        if any(keyword in text for keyword in ["话费", "充值", "流量", "宽带", "通讯",
                                                   "移动", "联通", "电信"]):
            return "通讯话费"

        # 娱乐类
        if any(keyword in text for keyword in ["电影", "ktv", "游戏", "视频", "音乐", "娱乐",
                                                   "腾讯视频", "爱奇艺", "优酷", "哔哩哔哩",
                                                   "bilibili", "抖音", "快手", "斗鱼", "虎牙",
                                                   "公园", "花海", "景区", "游乐园", "景点",
                                                   "门票", "百草园"]):
            return "休闲娱乐"

        # 医疗类
        if any(keyword in text for keyword in ["医院", "药店", "诊所", "医疗", "健康",
                                                   "药房", "养生", "体检"]):
            return "医疗健康"

        # 水电煤
        if any(keyword in text for keyword in ["电费", "水费", "燃气", "水电网", "缴费",
                                                   "国家电网", "南方电网"]):
            return "水电煤"

        # 房屋物业
        if any(keyword in text for keyword in ["房租", "物业", "住房", "房产",
                                                   "自如", "贝壳", "链家"]):
            return "房屋物业"

        # 根据交易类型直接判断
        if trans_type == "商户消费":
            # 尝试从商品描述或对方推断
            if counterparty and counterparty != "/":
                # 使用对方名称作为线索
                return self._infer_from_counterparty(counterparty, product)

        return "未分类"

    def _infer_from_counterparty(self, counterparty: str, product: str) -> str:
        """从对方名称推断分类"""
        text = f"{counterparty} {product}".lower()

        # 交通出行（优先检查）
        if any(kw in text for kw in ["12306", "铁路", "火车", "高铁", "机票", "航空",
                                         "携程", "去哪儿", "同程", "飞猪", "途牛",
                                         "中铁", "铁旅", "客运"]):
            return "交通出行"

        # 教育类（优先检查，避免与"料理"等词冲突）
        if any(kw in text for kw in ["大学", "学院", "学校", "教育", "培训",
                                         "学习", "课程", "书店", "考试", "报名",
                                         "学而思", "新东方", "网易云课堂",
                                         "慕课", "腾讯课堂", "打印"]):
            return "教育培训"

        # 餐饮（包含中餐类型，避免使用单独的"理"字）
        if any(kw in text for kw in ["餐饮", "咖啡", "茶", "麦当劳", "肯德基", "星巴克",
                                         "汉堡", "披萨", "喜茶", "奈雪", "瑞幸", "必胜客",
                                         "海底捞", "霸王茶姬", "茶百道", "蜜雪冰城",
                                         "华莱士", "沪上阿姨", "串串", "火锅", "烧烤",
                                         "烤肉", "小吃", "面馆", "米粉", "麻辣烫",
                                         "料理店", "日本料理", "韩国料理"]):
            return "餐饮美食"

        # 超市购物（增加"超级市场"等关键词）
        if any(kw in text for kw in ["超市", "便利店", "超级市场", "卖场",
                                         "屈臣氏", "沃尔玛", "家乐福", "永辉",
                                         "盒马", "苏果", "大润发", "物美", "ole", "山姆",
                                         "美宜佳", "罗森", "7-11", "全家", "壹度",
                                         "苏宁", "国美", "华润"]):
            return "购物消费"

        # 电商平台
        if any(kw in text for kw in ["京东", "淘宝", "天猫", "拼多多", "抖音电商",
                                         "小红书", "苏宁", "国美"]):
            return "购物消费"

        # 生活日用
        if any(kw in text for kw in ["日用", "家居", "生活", "零食", "有鸣", "售货机",
                                         "文体", "文体店", "电动车"]):
            return "生活日用"

        # 服饰美容
        if any(kw in text for kw in ["服装", "服饰", "鞋", "帽", "bag", "shop", "store",
                                         "美容", "美发", "美甲", "化妆", "护肤品"]):
            return "服饰美容"

        # 打车单车
        if any(kw in text for kw in ["出行", "交通", "打车", "单车", "停车", "加油",
                                         "哈啰", "青桔", "美团骑行", "摩拜", "滴滴"]):
            return "交通出行"

        # 通讯话费
        if any(kw in text for kw in ["话费", "充值", "流量", "宽带", "通讯",
                                         "移动", "联通", "电信"]):
            return "通讯话费"

        # 娱乐
        if any(kw in text for kw in ["电影", "ktv", "游戏", "视频", "音乐", "娱乐",
                                         "腾讯视频", "爱奇艺", "优酷", "bilibili",
                                         "抖音", "快手", "斗鱼", "虎牙",
                                         "公园", "花海", "景区", "游乐园", "景点", "门票",
                                         "百草园"]):
            return "休闲娱乐"

        return "未分类"

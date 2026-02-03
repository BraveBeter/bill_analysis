"""
创建示例账单数据脚本

用于生成测试用的模拟账单数据
"""

import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def create_sample_alipay():
    """创建示例支付宝账单"""
    np.random.seed(42)

    # 生成2024年的数据
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    days = (end_date - start_date).days

    data = []
    categories = ["餐饮美食", "购物消费", "交通出行", "休闲娱乐", "医疗健康", "教育培训"]

    for i in range(500):
        # 随机日期
        random_days = np.random.randint(0, days)
        transaction_time = start_date + timedelta(days=random_days, hours=np.random.randint(8, 22))

        # 随机分类
        category = np.random.choice(categories)

        # 根据分类设置金额范围
        if category == "餐饮美食":
            amount = np.random.uniform(20, 200)
            merchants = ["肯德基", "麦当劳", "星巴克", "美团外卖", "饿了么", "真功夫"]
        elif category == "购物消费":
            amount = np.random.uniform(50, 500)
            merchants = ["淘宝", "京东", "天猫", "拼多多", "苏宁", "优衣库"]
        elif category == "交通出行":
            amount = np.random.uniform(5, 100)
            merchants = ["滴滴出行", "地铁", "公交", "共享单车", "加油站", "停车场"]
        elif category == "休闲娱乐":
            amount = np.random.uniform(30, 300)
            merchants = ["爱奇艺", "腾讯视频", "Steam", "电影院", "KTV", "健身房"]
        elif category == "医疗健康":
            amount = np.random.uniform(50, 500)
            merchants = ["医院", "药店", "诊所", "体检中心"]
        else:
            amount = np.random.uniform(100, 1000)
            merchants = ["在线教育", "培训机构", "书店", "知识付费"]

        merchant = np.random.choice(merchants)

        data.append({
            "付款时间": transaction_time.strftime("%Y-%m-%d %H:%M:%S"),
            "交易分类": category,
            "交易对方": merchant,
            "商品说明": f"{merchant}消费",
            "金额（元）": -round(amount, 2),
            "收/支": "支出",
            "交易状态": "交易成功",
        })

    df = pd.DataFrame(data)
    df = df.sort_values("付款时间").reset_index(drop=True)

    return df


def create_sample_wechat():
    """创建示例微信账单"""
    np.random.seed(43)

    # 生成2024年的数据
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    days = (end_date - start_date).days

    data = []
    categories = ["餐饮", "购物", "交通", "娱乐", "医疗"]

    for i in range(400):
        random_days = np.random.randint(0, days)
        transaction_time = start_date + timedelta(days=random_days, hours=np.random.randint(8, 22))

        category = np.random.choice(categories)

        if category == "餐饮":
            amount = np.random.uniform(20, 150)
            merchants = ["瑞幸咖啡", "喜茶", "海底捞", "西贝", "外卖"]
        elif category == "购物":
            amount = np.random.uniform(50, 400)
            merchants = ["京东", "拼多多", "超市", "便利店"]
        elif category == "交通":
            amount = np.random.uniform(3, 80)
            merchants = ["滴滴", "地铁", "停车费", "加油"]
        elif category == "娱乐":
            amount = np.random.uniform(30, 200)
            merchants = ["视频会员", "游戏充值", "电影院"]
        else:
            amount = np.random.uniform(50, 400)
            merchants = ["医院", "药店"]

        merchant = np.random.choice(merchants)

        data.append({
            "交易时间": transaction_time.strftime("%Y-%m-%d %H:%M:%S"),
            "交易类型": "消费",
            "交易对方": merchant,
            "商品说明": f"{merchant}消费",
            "金额（元）": -round(amount, 2),
            "收/支": "支出",
            "交易状态": "支付成功",
        })

    df = pd.DataFrame(data)
    df = df.sort_values("交易时间").reset_index(drop=True)

    return df


def create_sample_ccb():
    """创建示例建设银行账单"""
    np.random.seed(44)

    # 生成2024年的数据
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    days = (end_date - start_date).days

    data = []

    # 银行卡消费（较少，主要用于大额消费）
    for i in range(100):
        random_days = np.random.randint(0, days)
        transaction_time = start_date + timedelta(days=random_days)

        amount = np.random.uniform(100, 2000)

        merchants = ["超市", "电器城", "加油站", "酒店", "餐厅"]
        merchant = np.random.choice(merchants)

        data.append({
            "交易时间": transaction_time.strftime("%Y-%m-%d"),
            "交易金额": -round(amount, 2),
            "交易对方": merchant,
            "交易类型": "消费",
            "商品": merchant + "消费",
        })

    df = pd.DataFrame(data)
    df = df.sort_values("交易时间").reset_index(drop=True)

    return df


def main():
    """生成所有示例数据"""
    print("正在生成示例账单数据...")

    # 创建输入目录
    input_dir = "data/input"
    os.makedirs(input_dir, exist_ok=True)

    # 生成支付宝账单
    print("  → 生成支付宝账单...")
    alipay_df = create_sample_alipay()
    alipay_path = os.path.join(input_dir, "alipay.csv")
    alipay_df.to_csv(alipay_path, index=False, encoding="utf-8-sig")
    print(f"    已保存: {alipay_path} ({len(alipay_df)} 条记录)")

    # 生成微信账单
    print("  → 生成微信账单...")
    wechat_df = create_sample_wechat()
    wechat_path = os.path.join(input_dir, "wechat_2024.xlsx")
    wechat_df.to_excel(wechat_path, index=False)
    print(f"    已保存: {wechat_path} ({len(wechat_df)} 条记录)")

    # 生成建设银行账单
    print("  → 生成建设银行账单...")
    ccb_df = create_sample_ccb()
    ccb_path = os.path.join(input_dir, "ccb.xls")
    ccb_df.to_excel(ccb_path, index=False)
    print(f"    已保存: {ccb_path} ({len(ccb_df)} 条记录)")

    print("\n✓ 示例数据生成完成！")
    print(f"\n你可以运行以下命令开始分析:")
    print(f"  uv run python -m bill_analysis.main")


if __name__ == "__main__":
    main()

"""可视化模块"""

import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
import pandas as pd
from typing import Dict, Optional
import os
import platform


def _setup_chinese_font():
    """配置中文字体"""
    # 获取系统可用字体
    system_fonts = [f.name for f in fm.fontManager.ttflist]

    # 定义常见中文字体列表（按优先级）
    chinese_fonts = []

    if platform.system() == "Windows":
        chinese_fonts = [
            "Microsoft YaHei",
            "SimHei",
            "SimSun",
            "KaiTi",
            "FangSong",
            "STXihei",
            "STSong",
            "STKaiti",
            "STFangsong",
        ]
    elif platform.system() == "Darwin":  # macOS
        chinese_fonts = [
            "PingFang SC",
            "Heiti SC",
            "STHeiti",
            "Hiragino Sans GB",
            "Microsoft YaHei",
        ]
    else:  # Linux
        chinese_fonts = [
            "WenQuanYi Micro Hei",
            "WenQuanYi Zen Hei",
            "Noto Sans CJK SC",
            "Source Han Sans SC",
            "Droid Sans Fallback",
        ]

    # 找到第一个可用的中文字体
    available_font = None
    for font in chinese_fonts:
        if font in system_fonts:
            available_font = font
            break

    # 如果没有找到中文字体，尝试直接设置
    if available_font:
        matplotlib.rcParams["font.sans-serif"] = [available_font] + matplotlib.rcParams["font.sans-serif"]
        print(f"✓ 使用中文字体: {available_font}")
    else:
        print("⚠ 警告: 未找到合适的中文字体，图表可能无法正确显示中文")
        print(f"  系统可用字体: {len(system_fonts)} 个")
        # 仍然尝试设置常见字体
        matplotlib.rcParams["font.sans-serif"] = chinese_fonts + matplotlib.rcParams["font.sans-serif"]

    matplotlib.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题


# 初始化时设置中文字体
_setup_chinese_font()


class Visualizer:
    """图表生成器"""

    def __init__(self, output_dir: str = "data/output"):
        """
        初始化可视化器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 设置样式（在样式设置后重新配置字体）
        try:
            plt.style.use("seaborn-v0_8-darkgrid")
        except OSError:
            # 如果 seaborn 样式不可用，使用默认样式
            plt.style.use("seaborn-v0_8-dark")

        # 重新确保中文字体设置（样式可能会覆盖）
        _setup_chinese_font()

    def plot_category_pie(self, category_data: Dict, filename: str = "category_pie.png") -> str:
        """
        绘制消费分类饼图

        Args:
            category_data: 分类数据 {分类名: {amount: 金额}}
            filename: 输出文件名

        Returns:
            输出文件完整路径
        """
        # 准备数据
        categories = []
        amounts = []

        for category, stats in category_data.items():
            if stats["amount"] > 0:
                categories.append(category)
                amounts.append(stats["amount"])

        if not categories:
            return ""

        # 创建饼图
        fig, ax = plt.subplots(figsize=(12, 8))

        colors = plt.cm.Set3(range(len(categories)))

        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=categories,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
            textprops={"fontsize": 10},
        )

        # 美化标签
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")

        ax.set_title("消费分类占比", fontsize=16, fontweight="bold", pad=20)

        # 添加图例
        ax.legend(
            wedges,
            [f"{cat}: ¥{amt:.2f}" for cat, amt in zip(categories, amounts)],
            title="消费金额",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
        )

        plt.tight_layout()

        # 保存图片
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return output_path

    def plot_monthly_trend(self, monthly_data: Dict, filename: str = "monthly_trend.png") -> str:
        """
        绘制月度消费趋势图

        Args:
            monthly_data: 月度数据 {年月: {amount: 金额}}
            filename: 输出文件名

        Returns:
            输出文件完整路径
        """
        # 准备数据
        months = sorted(monthly_data.keys())
        amounts = [abs(monthly_data[m]["amount"]) for m in months]

        if not months:
            return ""

        # 创建折线图
        fig, ax = plt.subplots(figsize=(14, 7))

        # 绘制折线
        ax.plot(
            months,
            amounts,
            marker="o",
            linewidth=2,
            markersize=8,
            color="#2E86AB",
            label="月度消费",
        )

        # 添加填充
        ax.fill_between(months, amounts, alpha=0.3, color="#2E86AB")

        # 添加柱状图
        bars = ax.bar(months, amounts, alpha=0.5, color="#A23B72")

        # 标注数值
        for bar, amount in zip(bars, amounts):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"¥{amount:.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_xlabel("月份", fontsize=12, fontweight="bold")
        ax.set_ylabel("消费金额（元）", fontsize=12, fontweight="bold")
        ax.set_title("月度消费趋势", fontsize=16, fontweight="bold", pad=20)

        # 旋转 x 轴标签
        plt.xticks(rotation=45, ha="right")

        # 添加网格
        ax.grid(True, alpha=0.3, linestyle="--")

        # 添加平均线
        avg_amount = sum(amounts) / len(amounts)
        ax.axhline(
            y=avg_amount,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"平均消费: ¥{avg_amount:.2f}",
        )

        ax.legend(loc="upper right")

        plt.tight_layout()

        # 保存图片
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return output_path

    def plot_platform_comparison(
        self, platform_data: Dict, filename: str = "platform_comparison.png"
    ) -> str:
        """
        绘制平台消费对比图

        Args:
            platform_data: 平台数据 {平台名: {amount: 金额}}
            filename: 输出文件名

        Returns:
            输出文件完整路径
        """
        # 准备数据
        platforms = list(platform_data.keys())
        amounts = [abs(platform_data[p]["amount"]) for p in platforms]

        if not platforms:
            return ""

        # 创建柱状图
        fig, ax = plt.subplots(figsize=(10, 6))

        colors = plt.cm.Set2(range(len(platforms)))

        bars = ax.bar(platforms, amounts, color=colors)

        # 标注数值
        for bar, amount in zip(bars, amounts):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"¥{amount:.2f}",
                ha="center",
                va="bottom",
                fontsize=12,
                fontweight="bold",
            )

        ax.set_xlabel("支付平台", fontsize=12, fontweight="bold")
        ax.set_ylabel("消费金额（元）", fontsize=12, fontweight="bold")
        ax.set_title("各平台消费对比", fontsize=16, fontweight="bold", pad=20)

        # 添加网格
        ax.grid(True, axis="y", alpha=0.3, linestyle="--")

        plt.tight_layout()

        # 保存图片
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return output_path

    def plot_top_merchants(
        self, merchants: list, filename: str = "top_merchants.png", top_n: int = 10
    ) -> str:
        """
        绘制消费最多的商户

        Args:
            merchants: 商户列表 [{"merchant": 名称, "amount": 金额}]
            filename: 输出文件名
            top_n: 显示前 N 个

        Returns:
            输出文件完整路径
        """
        if not merchants:
            return ""

        # 取前 N 个
        top_merchants = merchants[:top_n]

        # 准备数据
        merchant_names = [m["merchant"][:15] + "..." if len(m["merchant"]) > 15 else m["merchant"]
                          for m in top_merchants]
        amounts = [m["amount"] for m in top_merchants]

        # 创建水平柱状图
        fig, ax = plt.subplots(figsize=(12, 8))

        y_pos = range(len(merchant_names))

        bars = ax.barh(y_pos, amounts, color="#F18F01")

        # 标注数值
        for i, (bar, amount) in enumerate(zip(bars, amounts)):
            width = bar.get_width()
            ax.text(
                width,
                bar.get_y() + bar.get_height() / 2.0,
                f" ¥{amount:.2f}",
                ha="left",
                va="center",
                fontsize=10,
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(merchant_names)
        ax.invert_yaxis()
        ax.set_xlabel("消费金额（元）", fontsize=12, fontweight="bold")
        ax.set_title(f"消费最多的 {top_n} 个商户", fontsize=16, fontweight="bold", pad=20)

        # 添加网格
        ax.grid(True, axis="x", alpha=0.3, linestyle="--")

        plt.tight_layout()

        # 保存图片
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return output_path

    def plot_all_charts(self, analysis_result: Dict) -> Dict[str, str]:
        """
        生成所有图表

        Args:
            analysis_result: 分析结果

        Returns:
            生成的图表文件路径字典
        """
        charts = {}

        # 消费分类饼图
        if analysis_result.get("by_category"):
            charts["category_pie"] = self.plot_category_pie(analysis_result["by_category"])

        # 月度消费趋势图
        if analysis_result.get("by_month"):
            charts["monthly_trend"] = self.plot_monthly_trend(analysis_result["by_month"])

        # 平台消费对比图
        if analysis_result.get("by_platform"):
            charts["platform_comparison"] = self.plot_platform_comparison(
                analysis_result["by_platform"]
            )

        # 消费最多的商户
        if analysis_result.get("top_merchants"):
            charts["top_merchants"] = self.plot_top_merchants(analysis_result["top_merchants"])

        return charts

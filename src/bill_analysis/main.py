"""主程序入口"""

import io
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from bill_analysis.parsers import AlipayParser, WechatParser, CCBParser
from bill_analysis.processors import DataCleaner, Deduplicator, TransactionClassifier
from bill_analysis.analyzers import StatisticsAnalyzer
from bill_analysis.reports import ReportGenerator


class BillAnalyzer:
    """账单分析器"""

    def __init__(self, input_dir: str, output_dir: str, year: int = None):
        """
        初始化分析器

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            year: 分析年份（None 表示全部）
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.year = year or datetime.now().year

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 初始化各模块
        self.alipay_parser = AlipayParser()
        self.wechat_parser = WechatParser()
        self.ccb_parser = CCBParser()
        self.cleaner = DataCleaner()
        self.deduplicator = Deduplicator()
        self.classifier = TransactionClassifier()
        self.analyzer = StatisticsAnalyzer()
        self.report_generator = ReportGenerator(output_dir)

    def run(self) -> dict:
        """
        运行分析流程

        Returns:
            分析结果
        """
        print("=" * 60)
        print(f"开始分析账单数据 (年份: {self.year})")
        print("=" * 60)

        # 1. 读取账单数据
        print("\n[1/7] 正在读取账单数据...")
        all_transactions = self._load_all_bills()

        if all_transactions.empty:
            print("错误: 未找到任何账单数据！")
            print(f"请确保账单文件放在 {self.input_dir} 目录下")
            return {}

        print(f"   ✓ 共读取 {len(all_transactions)} 条交易记录")

        # 2. 清洗数据
        print("\n[2/7] 正在清洗数据...")
        cleaned = self.cleaner.clean(all_transactions)
        print(f"   ✓ 清洗后剩余 {len(cleaned)} 条有效交易记录")

        # 3. 去重
        print("\n[3/7] 正在去重...")
        deduped, duplicates = self.deduplicator.deduplicate(cleaned)
        duplicate_count = len(duplicates)
        duplicate_amount = duplicates["金额"].sum() if not duplicates.empty else 0
        print(f"   ✓ 去除 {duplicate_count} 条重复记录 (¥{abs(duplicate_amount):.2f})")
        print(f"   ✓ 去重后剩余 {len(deduped)} 条交易记录")

        # 4. 分类
        print("\n[4/7] 正在进行交易分类...")
        classified = self.classifier.classify(deduped)
        print(f"   ✓ 分类完成")

        # 5. 统计分析
        print("\n[5/7] 正在进行统计分析...")
        analysis_result = self.analyzer.analyze(classified, self.year)
        print(f"   ✓ 总支出: ¥{analysis_result['summary']['total_amount']:.2f}")
        print(f"   ✓ 交易笔数: {analysis_result['summary']['total_transactions']}")

        # 6. 生成图表
        print("\n[6/7] 正在生成可视化图表...")
        charts = self.report_generator.visualizer.plot_all_charts(analysis_result)
        print(f"   ✓ 生成 {len(charts)} 个图表")

        # 7. 生成报告
        print("\n[7/7] 正在生成报告...")
        reports = self.report_generator.generate_all_reports(analysis_result, classified)
        print(f"   ✓ 报告已生成:")

        for report_type, report_path in reports.items():
            if report_path:
                print(f"     - {report_type}: {report_path}")

        # 打印摘要
        self._print_summary(analysis_result)

        return {
            "transactions": classified,
            "analysis": analysis_result,
            "reports": reports,
            "charts": charts,
        }

    def _load_all_bills(self) -> pd.DataFrame:
        """加载所有账单数据"""
        all_data = []

        # 尝试加载支付宝账单
        alipay_file = os.path.join(self.input_dir, "alipay.csv")
        if os.path.exists(alipay_file):
            try:
                print(f"   → 正在读取支付宝账单: {alipay_file}")
                alipay_data = self.alipay_parser.parse(alipay_file)
                all_data.append(alipay_data)
                print(f"     读取 {len(alipay_data)} 条支付宝记录")
            except Exception as e:
                print(f"     警告: 读取支付宝账单失败 - {e}")
        else:
            print(f"   → 未找到支付宝账单 (alipay.csv)")

        # 尝试加载微信账单
        wechat_files = list(Path(self.input_dir).glob("wechat_*.xlsx"))
        if wechat_files:
            try:
                for wechat_file in wechat_files:
                    print(f"   → 正在读取微信账单: {wechat_file.name}")
                    wechat_data = self.wechat_parser.parse(str(wechat_file))
                    all_data.append(wechat_data)
                    print(f"     读取 {len(wechat_data)} 条微信记录")
            except Exception as e:
                print(f"     警告: 读取微信账单失败 - {e}")
        else:
            print(f"   → 未找到微信账单 (wechat_*.xlsx)")

        # 尝试加载建设银行账单
        ccb_file = os.path.join(self.input_dir, "ccb.xls")
        if os.path.exists(ccb_file):
            try:
                print(f"   → 正在读取建设银行账单: {ccb_file}")
                ccb_data = self.ccb_parser.parse(ccb_file)
                all_data.append(ccb_data)
                print(f"     读取 {len(ccb_data)} 条建设银行记录")
            except Exception as e:
                print(f"     警告: 读取建设银行账单失败 - {e}")
        else:
            print(f"   → 未找到建设银行账单 (ccb.xls)")

        # 合并所有数据
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            # 按时间排序
            combined = combined.sort_values("时间").reset_index(drop=True)
            return combined
        else:
            return pd.DataFrame()

    def _print_summary(self, analysis_result: dict):
        """打印分析摘要"""
        print("\n" + "=" * 60)
        print("分析摘要")
        print("=" * 60)

        summary = analysis_result["summary"]
        print(f"\n总支出: ¥{summary['total_amount']:.2f}")
        print(f"交易笔数: {summary['total_transactions']}")
        print(f"平均消费: ¥{summary['average_amount']:.2f}")

        # 分类统计
        by_category = analysis_result.get("by_category", {})
        if by_category:
            print(f"\n消费分类 (Top 5):")
            for i, (category, stats) in enumerate(
                sorted(by_category.items(), key=lambda x: x[1]["amount"], reverse=True)[:5], 1
            ):
                print(f"  {i}. {category}: ¥{stats['amount']:.2f} ({stats['count']} 笔)")

        # 平台统计
        by_platform = analysis_result.get("by_platform", {})
        if by_platform:
            print(f"\n平台消费:")
            for platform, stats in by_platform.items():
                print(f"  {platform}: ¥{stats['amount']:.2f} ({stats['count']} 笔)")

        print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="年度账单分析工具")
    parser.add_argument(
        "--input-dir",
        "-i",
        default="data/input",
        help="输入目录（默认: data/input）",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="data/output",
        help="输出目录（默认: data/output）",
    )
    parser.add_argument(
        "--year",
        "-y",
        type=int,
        default=None,
        help="分析年份（默认: 当年）",
    )

    args = parser.parse_args()

    # 创建分析器
    analyzer = BillAnalyzer(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        year=args.year,
    )

    # 运行分析
    try:
        result = analyzer.run()
        if result:
            print("\n✓ 分析完成！")
            return 0
        else:
            print("\n✗ 分析失败！")
            return 1
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

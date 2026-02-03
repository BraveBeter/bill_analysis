"""报告生成模块"""

import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import os
from .visualizer import Visualizer


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str = "data/output"):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.visualizer = Visualizer(output_dir)

    def generate_html_report(
        self, analysis_result: Dict, df: pd.DataFrame, filename: str = "annual_report.html"
    ) -> str:
        """
        生成 HTML 格式的年度报告

        Args:
            analysis_result: 分析结果
            df: 清洗后的交易数据
            filename: 输出文件名

        Returns:
            输出文件完整路径
        """
        # 生成图表
        charts = self.visualizer.plot_all_charts(analysis_result)

        # 生成 HTML
        html_content = self._build_html_content(analysis_result, df, charts)

        # 保存文件
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def _build_html_content(
        self, analysis_result: Dict, df: pd.DataFrame, charts: Dict[str, str]
    ) -> str:
        """构建 HTML 内容"""

        summary = analysis_result.get("summary", {})
        by_category = analysis_result.get("by_category", {})
        by_platform = analysis_result.get("by_platform", {})
        by_month = analysis_result.get("by_month", {})
        top_merchants = analysis_result.get("top_merchants", [])

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>年度消费报告 - {summary.get('year', '全部')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}

        .card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}

        .card .value {{
            font-size: 2em;
            font-weight: bold;
        }}

        .chart-container {{
            text-align: center;
            margin: 30px 0;
        }}

        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        .data-table th,
        .data-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        .data-table th {{
            background: #667eea;
            color: white;
            font-weight: bold;
        }}

        .data-table tr:hover {{
            background: #f5f5f5;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #eee;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 10px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 年度消费报告</h1>
            <p>统计期间: {summary.get('date_range', (None, None))[0]} 至 {summary.get('date_range', (None, None))[1]}</p>
        </div>

        <div class="content">
            <!-- 摘要卡片 -->
            <div class="section">
                <h2 class="section-title">消费概览</h2>
                <div class="summary-cards">
                    <div class="card">
                        <h3>总支出</h3>
                        <div class="value">¥{summary.get('total_amount', 0):.2f}</div>
                    </div>
                    <div class="card">
                        <h3>交易笔数</h3>
                        <div class="value">{summary.get('total_transactions', 0)}</div>
                    </div>
                    <div class="card">
                        <h3>平均消费</h3>
                        <div class="value">¥{summary.get('average_amount', 0):.2f}</div>
                    </div>
                </div>
            </div>

            <!-- 消费分类饼图 -->
            {self._generate_category_section(by_category, charts.get('category_pie'))}

            <!-- 月度趋势图 -->
            {self._generate_monthly_section(by_month, charts.get('monthly_trend'))}

            <!-- 平台对比 -->
            {self._generate_platform_section(by_platform, charts.get('platform_comparison'))}

            <!-- 消费最多的商户 -->
            {self._generate_merchants_section(top_merchants, charts.get('top_merchants'))}

        </div>

        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>由年度账单分析工具自动生成</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_category_section(self, by_category: Dict, chart_path: Optional[str]) -> str:
        """生成分类部分"""
        if not by_category:
            return ""

        rows = ""
        for category, stats in sorted(by_category.items(), key=lambda x: x[1]["amount"], reverse=True):
            rows += f"""
            <tr>
                <td><span class="badge">{category}</span></td>
                <td>{stats['count']}</td>
                <td>¥{stats['amount']:.2f}</td>
                <td>¥{stats.get('average', 0):.2f}</td>
            </tr>
            """

        chart_img = f'<img src="{os.path.basename(chart_path)}" alt="消费分类饼图">' if chart_path else ""

        return f"""
        <div class="section">
            <h2 class="section-title">消费分类统计</h2>
            {f'<div class="chart-container">{chart_img}</div>' if chart_img else ''}
            <table class="data-table">
                <thead>
                    <tr>
                        <th>分类</th>
                        <th>交易次数</th>
                        <th>总金额</th>
                        <th>平均金额</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    def _generate_monthly_section(self, by_month: Dict, chart_path: Optional[str]) -> str:
        """生成月度部分"""
        if not by_month:
            return ""

        rows = ""
        for month in sorted(by_month.keys()):
            stats = by_month[month]
            rows += f"""
            <tr>
                <td>{month}</td>
                <td>{stats['count']}</td>
                <td>¥{stats['amount']:.2f}</td>
            </tr>
            """

        chart_img = f'<img src="{os.path.basename(chart_path)}" alt="月度消费趋势">' if chart_path else ""

        return f"""
        <div class="section">
            <h2 class="section-title">月度消费趋势</h2>
            {f'<div class="chart-container">{chart_img}</div>' if chart_img else ''}
            <table class="data-table">
                <thead>
                    <tr>
                        <th>月份</th>
                        <th>交易次数</th>
                        <th>消费金额</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    def _generate_platform_section(self, by_platform: Dict, chart_path: Optional[str]) -> str:
        """生成平台部分"""
        if not by_platform:
            return ""

        rows = ""
        for platform, stats in by_platform.items():
            rows += f"""
            <tr>
                <td>{platform}</td>
                <td>{stats['count']}</td>
                <td>¥{stats['amount']:.2f}</td>
            </tr>
            """

        chart_img = f'<img src="{os.path.basename(chart_path)}" alt="平台消费对比">' if chart_path else ""

        return f"""
        <div class="section">
            <h2 class="section-title">平台消费对比</h2>
            {f'<div class="chart-container">{chart_img}</div>' if chart_img else ''}
            <table class="data-table">
                <thead>
                    <tr>
                        <th>平台</th>
                        <th>交易次数</th>
                        <th>消费金额</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    def _generate_merchants_section(self, top_merchants: list, chart_path: Optional[str]) -> str:
        """生成商户部分"""
        if not top_merchants:
            return ""

        rows = ""
        for merchant in top_merchants[:20]:
            rows += f"""
            <tr>
                <td>{merchant['merchant']}</td>
                <td>{merchant['count']}</td>
                <td>¥{merchant['amount']:.2f}</td>
            </tr>
            """

        chart_img = f'<img src="{os.path.basename(chart_path)}" alt="消费最多的商户">' if chart_path else ""

        return f"""
        <div class="section">
            <h2 class="section-title">消费最多的商户 (Top 20)</h2>
            {f'<div class="chart-container">{chart_img}</div>' if chart_img else ''}
            <table class="data-table">
                <thead>
                    <tr>
                        <th>商户</th>
                        <th>交易次数</th>
                        <th>消费金额</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    def export_to_csv(self, df: pd.DataFrame, filename: str = "cleaned_transactions.csv") -> str:
        """
        导出清洗后的数据到 CSV

        Args:
            df: 交易数据
            filename: 输出文件名

        Returns:
            输出文件完整路径
        """
        output_path = os.path.join(self.output_dir, filename)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    def generate_all_reports(
        self, analysis_result: Dict, df: pd.DataFrame
    ) -> Dict[str, str]:
        """
        生成所有报告

        Args:
            analysis_result: 分析结果
            df: 清洗后的交易数据

        Returns:
            生成的报告文件路径字典
        """
        reports = {}

        # HTML 报告
        reports["html_report"] = self.generate_html_report(analysis_result, df)

        # CSV 数据
        reports["csv_data"] = self.export_to_csv(df)

        return reports

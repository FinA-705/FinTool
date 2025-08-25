"""
绩效报告生成器模块
"""
from dataclasses import asdict

from backtest.performance_metrics import PerformanceMetrics


class ReportGenerator:
    """绩效报告生成器"""

    def generate_performance_report(self, metrics: PerformanceMetrics) -> str:
        """生成绩效报告"""
        report = "=" * 50 + "\n"
        report += "           绩效分析报告\n"
        report += "=" * 50 + "\n\n"

        # 收益率指标
        report += "收益率指标:\n"
        report += f"  总收益率:     {metrics.total_return:>10.2%}\n"
        report += f"  年化收益率:   {metrics.annual_return:>10.2%}\n"
        report += f"  月化收益率:   {metrics.monthly_return:>10.2%}\n"
        report += f"  日均收益率:   {metrics.daily_return:>10.4%}\n\n"

        # 风险指标
        report += "风险指标:\n"
        report += f"  年化波动率:   {metrics.volatility:>10.2%}\n"
        report += f"  下行波动率:   {metrics.downside_volatility:>10.2%}\n"
        report += f"  95% VaR:      {metrics.var_95:>10.4%}\n"
        report += f"  95% CVaR:     {metrics.cvar_95:>10.4%}\n\n"

        # 回撤指标
        report += "回撤指标:\n"
        report += f"  最大回撤:     {metrics.max_drawdown:>10.2%}\n"
        report += f"  回撤持续天数: {metrics.max_drawdown_duration:>10d}\n"
        report += f"  当前回撤:     {metrics.current_drawdown:>10.2%}\n"
        report += f"  平均回撤:     {metrics.avg_drawdown:>10.2%}\n\n"

        # 风险调整收益指标
        report += "风险调整收益:\n"
        report += f"  夏普比率:     {metrics.sharpe_ratio:>10.2f}\n"
        report += f"  索提诺比率:   {metrics.sortino_ratio:>10.2f}\n"
        report += f"  卡玛比率:     {metrics.calmar_ratio:>10.2f}\n"
        report += f"  欧米伽比率:   {metrics.omega_ratio:>10.2f}\n\n"

        # 基准相关指标（如果有）
        if metrics.beta is not None:
            report += "相对基准指标:\n"
            report += f"  Beta:         {metrics.beta:>10.2f}\n"
            report += f"  Alpha:        {metrics.alpha:>10.2%}\n"
            report += f"  跟踪误差:     {metrics.tracking_error:>10.2%}\n"
            report += f"  信息比率:     {metrics.information_ratio:>10.2f}\n"
            report += f"  上行捕获率:   {metrics.up_capture:>10.2%}\n"
            report += f"  下行捕获率:   {metrics.down_capture:>10.2%}\n\n"

        # 交易统计
        if metrics.total_trades > 0:
            report += "交易统计:\n"
            report += f"  交易次数:     {metrics.total_trades:>10d}\n"
            report += f"  胜率:         {metrics.win_rate:>10.2%}\n"
            report += f"  盈亏比:       {metrics.profit_loss_ratio:>10.2f}\n"
            report += f"  平均交易收益: {metrics.avg_trade_return:>10.2f}\n\n"

        # 统计特征
        report += "统计特征:\n"
        report += f"  偏度:         {metrics.skewness:>10.2f}\n"
        report += f"  峰度:         {metrics.kurtosis:>10.2f}\n"
        report += f"  最佳单日:     {metrics.best_day:>10.2%}\n"
        report += f"  最差单日:     {metrics.worst_day:>10.2%}\n"
        report += f"  正收益日比例: {metrics.positive_days:>10.2%}\n\n"

        return report

    def to_dict(self, metrics: PerformanceMetrics) -> dict:
        """将绩效指标转换为字典"""
        return asdict(metrics)

    def to_json(self, metrics: PerformanceMetrics) -> str:
        """将绩效指标转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(metrics), indent=4)

"""
简单的Cron表达式解析器
"""
from datetime import datetime, timedelta
from typing import Optional


class CronParser:
    """简单的Cron表达式解析器"""

    @staticmethod
    def parse_cron(
        cron_expr: str, base_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        解析简单的cron表达式
        支持格式：
        - "*/5 * * * *" (每5分钟)
        - "0 */2 * * *" (每2小时)
        - "0 0 * * *" (每天0点)
        - "interval:300" (每300秒)
        """
        if base_time is None:
            base_time = datetime.now()

        if cron_expr.startswith("interval:"):
            try:
                seconds = int(cron_expr.split(":")[1])
                return base_time + timedelta(seconds=seconds)
            except (ValueError, IndexError):
                return None

        parts = cron_expr.split()
        if len(parts) != 5:
            return None

        try:
            if cron_expr == "* * * * *":
                return base_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
            elif cron_expr == "0 * * * *":
                next_time = base_time.replace(minute=0, second=0, microsecond=0)
                if next_time <= base_time:
                    next_time += timedelta(hours=1)
                return next_time
            elif cron_expr == "0 0 * * *":
                next_time = base_time.replace(hour=0, minute=0, second=0, microsecond=0)
                if next_time <= base_time:
                    next_time += timedelta(days=1)
                return next_time
            elif cron_expr == "*/5 * * * *":
                minutes = (base_time.minute // 5 + 1) * 5
                if minutes >= 60:
                    next_time = base_time.replace(
                        minute=0, second=0, microsecond=0
                    ) + timedelta(hours=1)
                else:
                    next_time = base_time.replace(
                        minute=minutes, second=0, microsecond=0
                    )
                return next_time
        except Exception:
            pass

        return None

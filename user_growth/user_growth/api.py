"""大屏数据接口（免登录）。

只输出聚合统计与脱敏信息，不暴露手机号等个人明细字段。
"""

from datetime import datetime

import frappe

from user_growth.analytics import (
	active_rows,
	count_by,
	month_axis,
	monthly_series,
	recent_churn,
)

DOCTYPE = "User Service Record"


@frappe.whitelist(allow_guest=True)
def get_dashboard_data():
	rows = frappe.get_all(
		DOCTYPE,
		fields=[
			"user_name",
			"plan_type",
			"monthly_fee",
			"activation_date",
			"churn_date",
			"province",
			"channel",
		],
		limit_page_length=0,
	)

	series = monthly_series(rows, month_axis(24))
	last = series[-1] if series else {}
	kpi = {
		"active_users": last.get("active_end", 0),
		"total_users": len(rows),
		"new_this_month": last.get("new", 0),
		"churned_this_month": last.get("churned", 0),
		"net_this_month": last.get("net", 0),
		"churn_rate": last.get("churn_rate", 0),
		"mrr": last.get("mrr", 0),
	}

	actives = active_rows(rows)
	return {
		"kpi": kpi,
		"monthly": series,
		"province": count_by(actives, "province"),
		"plan": count_by(actives, "plan_type"),
		"channel": count_by(actives, "channel"),
		"recent_churn": recent_churn(rows),
		"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
	}

import frappe
from frappe import _
from frappe.utils import getdate

from user_growth.analytics import month_axis_between, monthly_series

DOCTYPE = "User Service Record"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	rows = _filtered_rows(filters)
	months = month_axis_between(filters.get("from_date"), filters.get("to_date"))
	data = [frappe._dict(row) for row in monthly_series(rows, months)]
	if data:
		data.append(_summary_row(data))
	return get_columns(), data, None, _build_chart(data)


def _build_chart(data):
	"""末行是汇总行，图表只用逐月序列。"""
	series = [r for r in data if r.get("month") not in (None, "", "合计/月末")]
	if not series:
		return None
	return {
		"type": "line",
		"data": {
			"labels": [r["month"] for r in series],
			"datasets": [
				{"name": _("新增开通"), "values": [r["new"] for r in series]},
				{"name": _("流失"), "values": [r["churned"] for r in series]},
				{"name": _("净增"), "values": [r["net"] for r in series]},
			],
		},
	}


def _filtered_rows(filters):
	filters_list = [["activation_date", "<=", filters.get("to_date") or getdate()]]
	for field in ("province", "plan_type", "channel"):
		if filters.get(field):
			filters_list.append([field, "=", filters[field]])
	return frappe.get_all(
		DOCTYPE,
		filters=filters_list,
		fields=["plan_type", "monthly_fee", "activation_date", "churn_date", "province", "channel"],
		limit_page_length=0,
		order_by="activation_date asc",
	)


def _summary_row(data):
	total_new = sum(r["new"] for r in data)
	total_churned = sum(r["churned"] for r in data)
	avg_churn_rate = round(sum(r["churn_rate"] for r in data) / len(data), 1)
	return frappe._dict(
		month="合计/月末",
		opening=data[0]["opening"],
		new=total_new,
		churned=total_churned,
		net=total_new - total_churned,
		active_end=data[-1]["active_end"],
		churn_rate=avg_churn_rate,
		mrr=data[-1]["mrr"],
	)


def get_columns():
	return [
		{"label": _("月份"), "fieldname": "month", "fieldtype": "Data", "width": 95},
		{"label": _("期初在网"), "fieldname": "opening", "fieldtype": "Int", "width": 100},
		{"label": _("新增开通"), "fieldname": "new", "fieldtype": "Int", "width": 100},
		{"label": _("流失"), "fieldname": "churned", "fieldtype": "Int", "width": 90},
		{"label": _("净增"), "fieldname": "net", "fieldtype": "Int", "width": 90},
		{"label": _("期末在网"), "fieldname": "active_end", "fieldtype": "Int", "width": 100},
		{
			"label": _("流失率(%)"),
			"fieldname": "churn_rate",
			"fieldtype": "Percent",
			"precision": "1",
			"width": 110,
		},
		{"label": _("MRR(¥)"), "fieldname": "mrr", "fieldtype": "Currency", "width": 130},
	]

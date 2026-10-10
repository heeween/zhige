"""统计口径：报表与大屏共用的聚合计算。

月度指标口径：
- 期初在网 opening：当月 1 日 0 点仍处于在网状态的用户数
  （开通日期早于当月，且未流失或流失日期在当月及以后）；
- 新增 new：当月开通的记录数；
- 流失 churned：当月发生流失的记录数（含窗口期之前开通的用户）；
- 净增 net = 新增 - 流失；
- 期末在网 active_end = 期初在网 + 新增 - 流失；
- 流失率 churn_rate = 流失 / 期初在网 × 100%；
- MRR：月末仍处于在网状态的记录月费总额。
"""

import frappe
from frappe.utils import add_months, get_first_day, getdate

DOCTYPE = "User Service Record"


def month_axis(n_months):
	"""以当前月份为最后一月的 n 个月的月初序列（升序）。"""
	cursor = get_first_day(getdate())
	axis = []
	for _ in range(n_months):
		axis.append(cursor)
		cursor = add_months(cursor, -1)
	return list(reversed(axis))


def month_axis_between(from_date=None, to_date=None):
	"""从 from_date 所在月初到 to_date 所在月初的月初序列（升序）。"""
	start = get_first_day(getdate(from_date)) if from_date else None
	end = get_first_day(getdate(to_date)) if to_date else get_first_day(getdate())
	if not start:
		start = add_months(end, -23)
	axis, cursor = [], start
	while cursor <= end:
		axis.append(cursor)
		cursor = add_months(cursor, 1)
	return axis


def _month_key(d):
	return d.strftime("%Y-%m")


def monthly_series(rows, months):
	"""把全量订阅行按月聚合为指标序列。"""
	axis_keys = [_month_key(m) for m in months]
	first_start = months[0]
	opening = 0
	new_by = dict.fromkeys(axis_keys, 0)
	churn_by = dict.fromkeys(axis_keys, 0)

	for r in rows:
		act = r["activation_date"]
		if act < first_start:
			if not r["churn_date"] or r["churn_date"] >= first_start:
				opening += 1
		elif _month_key(act) in new_by:
			new_by[_month_key(act)] += 1
		if r["churn_date"] and r["churn_date"] >= first_start:
			kc = _month_key(r["churn_date"])
			if kc in churn_by:
				churn_by[kc] += 1

	series = []
	prev_active = opening
	for m, key in zip(months, axis_keys, strict=True):
		month_end = add_months(m, 1)
		new, churned = new_by[key], churn_by[key]
		mrr = sum(
			r["monthly_fee"]
			for r in rows
			if r["activation_date"] < month_end
			and (not r["churn_date"] or r["churn_date"] >= month_end)
		)
		series.append(
			{
				"month": key,
				"opening": prev_active,
				"new": new,
				"churned": churned,
				"net": new - churned,
				"active_end": prev_active + new - churned,
				"churn_rate": round(churned / prev_active * 100, 1) if prev_active else 0,
				"mrr": mrr,
			}
		)
		prev_active += new - churned
	return series


def active_rows(rows):
	return [r for r in rows if not r["churn_date"]]


def count_by(rows, field):
	counts = {}
	for r in rows:
		counts[r[field]] = counts.get(r[field], 0) + 1
	return [{"name": k, "value": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


def recent_churn(rows, limit=20):
	churned = sorted(
		(r for r in rows if r["churn_date"]),
		key=lambda r: r["churn_date"],
		reverse=True,
	)[:limit]
	return [
		{
			"user": _mask(r["user_name"]),
			"province": r["province"],
			"plan_type": r["plan_type"],
			"monthly_fee": r["monthly_fee"],
			"churn_date": r["churn_date"].strftime("%m-%d") if r["churn_date"] else "",
		}
		for r in churned
	]


def _mask(name):
	return name[:1] + "**" if name else name

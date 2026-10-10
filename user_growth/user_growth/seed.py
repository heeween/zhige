"""Mock 数据种子：生成约 800 条、覆盖最近 24 个月的剧情化订阅记录。

剧情设定（让大屏曲线有起伏、可讲述）：
- 整体获客量逐月上升（20+/月 → 50/月）；
- 每年春季为淡季、秋季为旺季（季节性波动）；
- 约 11 个月前有一次"调价风波"，当月流失率冲高到 9%；
- 约 3 个月前有一场"大促拉新"，当月新增冲高约 35%；
- 约 12% 的流失用户会在 1~2 个月内回流重新开通（同一手机号多条记录）。

用法：
- 安装 App 后由 after_install 钩子自动执行（幂等：已有数据则跳过）；
- 手动重灌：bench --site <site> execute user_growth.seed.reset_and_seed
"""

import math
import random
from datetime import date, timedelta

import frappe
from frappe.utils import getdate

DOCTYPE = "User Service Record"

MONTHS = 24
TOTAL_MONTHLY_CHURN = 0.022  # 常态月流失率
CHURN_INCIDENT_MONTH = 13  # 从最早数起的第 14 个月：调价风波
CAMPAIGN_MONTH = 20  # 大促月份
REACTIVATION_RATE = 0.12

PLANS = [
	("基础版", 49, 52),
	("标准版", 99, 31),
	("旗舰版", 199, 17),
]
PROMO_FEES = {"基础版": 39, "标准版": 89, "旗舰版": 159}
ENTERPRISE_PLAN_WEIGHTS = {"基础版": 20, "标准版": 45, "旗舰版": 35}

CHANNELS = [
	("线上广告", 32),
	("地推", 24),
	("转介绍", 18),
	("自然流入", 26),
]

PROVINCES = [
	("广东省", 18),
	("江苏省", 12),
	("浙江省", 12),
	("北京市", 10),
	("山东省", 9),
	("四川省", 9),
	("河南省", 8),
	("湖北省", 8),
	("福建省", 7),
	("湖南省", 7),
]

SURNAMES = list("王李张刘陈杨赵黄周吴徐孙马朱胡郭何林罗郑梁谢宋唐许韩冯邓曹彭")
GIVEN = [
	"伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋",
	"勇", "艳", "杰", "娟", "涛", "明", "超", "霞", "平", "刚",
	"秀英", "文轩", "子涵", "雨欣", "浩然", "欣怡", "梓萱", "博文",
	"思远", "晓东", "建国", "志强", "文博", "天翔", "宇轩", "浩宇",
	"子墨", "一鸣", "佳琪", "梦琪", "雪梅", "丽华", "丹丹", "婷婷",
	"倩文", "思思", "雅静", "海燕", "冬梅", "桂芳",
]

PHONE_PREFIXES = [
	"133", "135", "136", "137", "138", "139", "150", "151", "152",
	"155", "157", "158", "159", "176", "177", "178", "180", "181",
	"185", "186", "187", "188", "189",
]

_rng = random.Random(20261010)
_used_phones = set()


def seed(force=False):
	"""灌入 mock 数据；已有数据且未指定 force 时幂等跳过。返回写入条数。"""
	if not force and frappe.db.count(DOCTYPE):
		return 0
	if force:
		frappe.db.delete(DOCTYPE)

	records = _generate_records()
	for i, row in enumerate(records, 1):
		frappe.get_doc(dict(doctype=DOCTYPE, **row)).insert(ignore_permissions=True)
		if i % 200 == 0:
			frappe.db.commit()
	frappe.db.commit()
	return len(records)


def reset_and_seed():
	"""清空并重新生成 mock 数据。"""
	seed(force=True)


def _generate_records():
	today = getdate()
	month_starts = _month_starts(MONTHS)
	active, records = [], []

	for idx, mstart in enumerate(month_starts):
		dim = _days_in_month(mstart.year, mstart.month)
		last_day = today.day if (mstart.year == today.year and mstart.month == today.month) else dim

		# 流失阶段：存量在网用户按当月流失率流失
		churn_rate = 0.09 if idx == CHURN_INCIDENT_MONTH else TOTAL_MONTHLY_CHURN + idx * 0.0003
		survivors, reactivations = [], []
		for user in active:
			if _rng.random() >= churn_rate:
				survivors.append(user)
				continue
			churn_day = _rand_day(mstart, last_day, after=user["activation_date"])
			if churn_day is None:
				survivors.append(user)
				continue
			user["status"] = "已流失"
			user["churn_date"] = churn_day
			records.append(user)
			if _rng.random() < REACTIVATION_RATE:
				back_day = churn_day + timedelta(days=_rng.randint(25, 60))
				if back_day < today:
					back = _new_user(back_day)
					back["user_name"], back["phone"] = user["user_name"], user["phone"]
					reactivations.append(back)
		active = survivors + reactivations

		# 获客阶段：线性增长 + 季节波动 + 大促冲量
		base_new = 20 + idx * 1.25
		seasonal = 1 + 0.16 * math.sin(2 * math.pi * ((idx % 12) + 2) / 12)
		multiplier = 1.35 if idx == CAMPAIGN_MONTH else 1.0
		n_new = max(5, int(base_new * seasonal * _rng.uniform(0.85, 1.15) * multiplier))
		for _ in range(n_new):
			day = _rand_day(mstart, last_day)
			if day:
				active.append(_new_user(day))

	records.extend(active)
	records.sort(key=lambda r: r["activation_date"])
	return records


def _month_starts(n):
	today = getdate()
	y, m = today.year, today.month
	starts = []
	for _ in range(n):
		starts.append(date(y, m, 1))
		m -= 1
		if m == 0:
			y, m = y - 1, 12
	return list(reversed(starts))


def _days_in_month(y, m):
	if m == 12:
		return 31
	return (date(y, m + 1, 1) - timedelta(days=1)).day


def _rand_day(mstart, last_day, after=None):
	"""当月随机一天；after 指定不早于其次日；当月没有合法日期时返回 None。"""
	lo = mstart.day
	hi = last_day
	if after is not None:
		lo = max(lo, after.day + 1) if (after.year, after.month) == (mstart.year, mstart.month) else lo
	if lo > hi:
		return None
	return date(mstart.year, mstart.month, _rng.randint(lo, hi))


def _new_user(day):
	customer = _weighted([("个人", 80), ("企业", 20)])
	if customer == "企业":
		plan = _weighted([(p, ENTERPRISE_PLAN_WEIGHTS[p]) for p, _, _ in PLANS])
	else:
		plan = _weighted([(p, w) for p, _, w in PLANS])
	fee = {p: f for p, f, _ in PLANS}[plan]
	if _rng.random() < 0.15:
		fee = PROMO_FEES[plan]
	return {
		"user_name": _rng.choice(SURNAMES) + _rng.choice(GIVEN),
		"phone": _gen_phone(),
		"customer_type": customer,
		"plan_type": plan,
		"monthly_fee": fee,
		"activation_date": day,
		"channel": _weighted(CHANNELS),
		"province": _weighted(PROVINCES),
		"status": "在网",
		"churn_date": None,
	}


def _gen_phone():
	while True:
		phone = _rng.choice(PHONE_PREFIXES) + "".join(str(_rng.randint(0, 9)) for _ in range(8))
		if phone not in _used_phones:
			_used_phones.add(phone)
			return phone


def _weighted(pairs):
	total = sum(w for _, w in pairs)
	x = _rng.uniform(0, total)
	for value, weight in pairs:
		x -= weight
		if x <= 0:
			return value
	return pairs[-1][0]

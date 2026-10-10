frappe.query_reports["User Growth Analysis"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("开始日期"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.month_start(frappe.datetime.get_today()), -11),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("结束日期"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "province",
			label: __("省份"),
			fieldtype: "Select",
			options: "\n广东省\n江苏省\n浙江省\n北京市\n山东省\n四川省\n河南省\n湖北省\n福建省\n湖南省",
		},
		{
			fieldname: "plan_type",
			label: __("套餐类型"),
			fieldtype: "Select",
			options: "\n基础版\n标准版\n旗舰版",
		},
		{
			fieldname: "channel",
			label: __("获客渠道"),
			fieldtype: "Select",
			options: "\n线上广告\n地推\n转介绍\n自然流入",
		},
	],
	formatter(value, row, column, data) {
		if (column.fieldname === "net" && value < 0) {
			return `<span style="color:#e11d48">${value}</span>`;
		}
		if (column.fieldname === "churn_rate" && value >= 5) {
			return `<span style="color:#e11d48;font-weight:600">${value}</span>`;
		}
		return value;
	},
};

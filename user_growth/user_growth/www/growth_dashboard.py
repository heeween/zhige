import frappe


def get_context(context):
	context.no_cache = 1
	context.title = "用户增长数据大屏"
	return context

import frappe
from frappe import _
from frappe.model.document import Document


class UserServiceRecord(Document):
	def validate(self):
		if self.status == "已流失":
			if not self.churn_date:
				frappe.throw(_("状态为「已流失」时必须填写流失日期"))
			if self.activation_date and self.churn_date <= self.activation_date:
				frappe.throw(_("流失日期必须晚于开通日期"))
		else:
			self.churn_date = None

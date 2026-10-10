import frappe


def after_install():
	from user_growth.seed import seed

	seed()
	frappe.db.commit()

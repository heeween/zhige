frappe.ui.form.on("User Service Record", {
	refresh(frm) {
		frm.set_query("province", () => ({}));
	},
});

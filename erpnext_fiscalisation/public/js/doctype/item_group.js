frappe.ui.form.on("Item Group", {
  refresh(frm) {
    frm.add_custom_button("Set HS Codes on Items", () => {
      if (frm.is_dirty() || frm.is_new()) {
        frappe.throw("Please save pending changes before proceeding.");
      } else {
        frappe.confirm(
          "Are you sure that you want to update the HS Code on linked items that do not yet have an HS Code set?",
          () => {
            frappe.call({
              method: "erpnext_fiscalisation.item_group.set_hs_codes_on_items",
              args: {
                group_name: frm.doc.name,
              },
            });
          },
          () => frappe.msgprint("Cancelled HS Code update.")
        );
      }
    });
  },
});

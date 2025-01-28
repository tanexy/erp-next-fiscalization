// Copyright (c) 2024, Eskill Trading (Pvt) Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fiscal Signature", {
  refresh(frm) {
    if (frappe.user.has_role("System Manager")) {
      if (frm.doc.is_retry) {
        frm.add_custom_button(__("Retry Fiscalisation"), () => {
          frappe.call({
            method: "retry_fiscalisation",
            doc: frm.doc,
            callback: () => frm.reload_doc(),
          });
        });
      }

      if (frm.doc.fiscal_harmony_id && !frm.doc.fdms_url) {
        frm.add_custom_button(__("Fetch Signing Data"), () => {
          frappe.call({
            method: "fetch_signing_data",
            doc: frm.doc,
            callback: () => frm.reload_doc(),
          });
        });
      }

      if (frm.doc.fiscal_harmony_filename) {
        frm.add_custom_button(__("Attach Fiscal PDF"), () => {
          frappe.call({
            method: "download_or_generate_pdf",
            doc: frm.doc,
          });
        });
      }
    }
  },
});
